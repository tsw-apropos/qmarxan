"""
/***************************************************************************
 QMarxan
                                 A QGIS plugin
 Create grid, calculate grid values, export Marxan input layers, import results
                             -------------------
        begin                : 2011-10-11
        copyright            : (C) 2011 by Apropos Information Systems Inc.
        email                : tsw@aproposinfosystems.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
def name():
    return "Qmarxan - Setup and export data to Marxan"
def description():
    return "Create grid, calculate grid values, export Marxan input layers, import results. Requires ftools, numpy, fiona & rasterstats."
def version():
    return "Version 1.3.1"
def icon():
    return "icons/qm_icon.png"
def qgisMinimumVersion():
    return "1.8"
def author():
    return "Apropos Information Systems Inc."
def email():
    return "info@aproposinfosystems.com"
def classFactory(iface):
    # load QMarxan class from file QMarxan
    from qmarxan import Qmarxan
    return Qmarxan(iface)
