# -*- coding utf-8 -*-

import os
from shutil import rmtree
from src.paths import output

def mk_folders(recibos_car):
    """
    Função para criar as pastas de acordo com o recibo car.

    :param recibos_car: lista contendo os recibos car
    """
    for folder in recibos_car:
        try:
            os.mkdir(
                os.path.join(
                    output,
                    folder
                )
            )
        except:
            rmtree(
                os.path.join(
                    output,
                    folder
                )
            )
            os.mkdir(
                os.path.join(
                    output,
                    folder
                )
            )