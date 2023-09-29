# -*- coding utf-8 -*-

import os

"""
Caminhos relevantes para o projeto.
"""

base_path = os.getcwd()

mapbiomas_2012 = os.path.join(
    base_path,
    r"src\dados\raster\brasil_coverage_2012.tif"
)

mapbiomas_2022 = os.path.join(
    base_path,
    r"src\dados\raster\brasil_coverage_2022.tif"
)

vector_car_mg = os.path.join(
    base_path,
    r"src\dados\vector\AREA_IMOVEL\AREA_IMOVEL.shp"
)

vector_vegnat = os.path.join(
    base_path,
    r"src\dados\vector\VEGETACAO_NATIVA\VEGETACAO_NATIVA.shp"
)

output = os.path.join(
    base_path,
    r"src\Resultados"
)