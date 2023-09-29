# -*- coding utf-8 -*-
"""
Script para avaliar conversões de vegetação nativa entre 2012 e 2022, de imóveis com CAR

Autor: Denis Leonardo Santos
"""
import rasterio
import rasterio.mask
import rasterio.plot
import rasterio.features
import fiona
import openpyxl
import geopandas as gpd
from pandas import concat,DataFrame
from tempfile import mkdtemp
from shutil import rmtree
from src.paths import *
from src.lists import *
from src.folders import *
import matplotlib.pyplot as plt

#Criando pasta temporária para salvar resultados intermediários
temp_dir = mkdtemp()

mk_folders(recibo_car)

def clip_mask(raster: str) -> None:
    """Função para realização do recorte do raster, de acordo com uma máscara vetorial do tipo oplígono.
    
    :param raster: Dado raster
    """
    #Máscaras (limite das propriedades) para utilizar no recorte do raster
    with fiona.open(os.path.join(temp_dir,"vector_wgs84_buffer.shp"), "r") as shp:
        shapes = [feature["geometry"] for feature in shp]

    #Recorte do raster, de acordo com as máscaras
    with rasterio.open(raster) as raster_2012:
        out_image, out_transform = rasterio.mask.mask(raster_2012, shapes, crop=True, filled=True)
        out_meta = raster_2012.meta

    #Setando parâmetros para salvar imagem
    out_meta.update({"driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform})

    #Salvando imagem temporária
    with rasterio.open(os.path.join(temp_dir, os.path.basename(raster).split(".")[0] + "_clip.tif"), "w", **out_meta) as dest:
        dest.write(out_image)
    #rasterio.plot.show(out_image)

def poligonize(raster: str) -> None:
    """
    Função responsável fazer a transformação de dados raster em dados vetoriais.
    """
    with rasterio.open(os.path.join(temp_dir, os.path.basename(raster).split(".")[0] + "_clip.tif")) as src:
        image = src.read()
        
        mask = None

        results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v)
            in enumerate(
                rasterio.features.shapes(image, mask=mask, transform=src.transform)))

    geoms = list(results)

    #Testando para veficar e nomear os usos de 2012 e 2022
    if "2012" in str(os.path.basename(raster).split(".")):
        dfg_poly = gpd.GeoDataFrame.from_features(geoms)
        dfg_poly.crs = "epsg: 4326"
        #salvando dados temporários, não nulos
        dfg_poly = dfg_poly.query("raster_val != 0")
        #salvando shp temporario
        dfg_poly.to_file(
            os.path.join(
                temp_dir,
                os.path.basename(raster)\
                    .split(".")[0] + "_use_2012.shp"
                )
            )
        #filtrando dados de floresta
        dfg_poly = dfg_poly.query("raster_val == 3")
        dfg_poly.to_file(
            os.path.join(
                temp_dir,
                os.path.basename(raster)\
                    .split(".")[0] + "_florest_2012.shp"
                )
            )
    else:
        dfg_poly = gpd.GeoDataFrame.from_features(geoms)
        dfg_poly.crs = "epsg: 4326"
        #filtrando dados não nulos
        dfg_poly = dfg_poly.query("raster_val != 0")
        dfg_poly.to_file(os.path.join(
                temp_dir,
                os.path.basename(raster)\
                    .split(".")[0] + "_use_2022.shp"
                ))
    #dfg_poly.plot()
    #plt.show()

#Abrindo e transformando os dados vetoriais para o mesmo sistema de referência
dfg_car = gpd.read_file(vector_car_mg).to_crs(31983)

#Filtrando os imóveis de interesse
dfg_car_filter = dfg_car.query("COD_IMOVEL in @recibo_car")

#Salvando como dados temporários para recorte do raster
dfg_buffer = dfg_car_filter.buffer(100)
dfg_buffer = dfg_buffer.to_crs(4326)
dfg_buffer.to_file(
    os.path.join(
        temp_dir,
        "vector_wgs84_buffer.shp"
    )
)

#Realizando o recorte das imagens
for img in images:
    clip_mask(img)
    poligonize(img)

#Importando poligonos dos raster poligonizados de 2012
dfg_use_2012 = gpd.read_file(
    os.path.join(
        temp_dir,
        os.path.basename(mapbiomas_2012).split(".")[0] + "_use_2012.shp"
    )
)\
    .to_crs(31983)

#Importando poligonos dos raster poligonizados de 2022
dfg_use_2022 = gpd.read_file(
    os.path.join(
        temp_dir,
        os.path.basename(mapbiomas_2022).split(".")[0] + "_use_2022.shp"
    )
)\
    .to_crs(31983)

#Realizando intersexção dos usos para observar as mudanças
inter_usos = dfg_use_2022.overlay(dfg_use_2012, how='intersection')

#Calculando conversao
inter_usos["conversao_ha"] = inter_usos.area/10000

#Trocando valores por suas descrições
#inter_usos = inter_usos.replace({"raster_val_2": mapbiomas_uso})
#inter_usos = inter_usos.replace({"raster_val_1": mapbiomas_uso})
resultado = gpd.GeoDataFrame()

#Calculando atributos solicitados e salvando em suas devidas pastas
for recibo in recibo_car:
    dfg_temp = dfg_car_filter.query("COD_IMOVEL in @recibo")
    inter_usos_clip = gpd.clip(inter_usos, dfg_temp)
    uso_sjoin = gpd.sjoin(inter_usos_clip, dfg_temp)
    propriedade = uso_sjoin.rename(columns = {
        "COD_IMOVEL": "recibo_car",
        "NOM_MUNICI":"municipio",
        "COD_ESTADO":"UF",
        "NUM_AREA": "area_prop",
        "raster_val_2": "uso_2012",
        "raster_val_1": "uso_2022",
        "conversao_ha": "conversao_ha"})
    propriedade = propriedade.dissolve(by = ["recibo_car", "uso_2012", "uso_2022"])
    conversao = propriedade.query("uso_2012 == 3")
    conversao = propriedade.query("uso_2012 == 3")
    propriedade = propriedade.drop(
        ["index_right", "NUM_MODULO", "TIPO_IMOVE", "SITUACAO", "CONDICAO_I"],
        axis = 1)
    propriedade.to_file(os.path.join(output, recibo, recibo + ".shp"))
    resultado = concat([resultado, propriedade])

#Salvando arquivo geral
resultado.to_file(os.path.join(output, "geral.shp"))
resultado.to_excel(
    os.path.join(
        output,
        "Relatório_geral.xlsx"
    )
)

#Deletando pasta temporária
rmtree(temp_dir, True)