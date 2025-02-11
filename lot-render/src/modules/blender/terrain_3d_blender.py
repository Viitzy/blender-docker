import bpy
from mathutils import Vector
import numpy as np

# import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from scipy.spatial import Delaunay
from scipy.spatial import KDTree
from scipy.interpolate import CubicSpline
import scipy.optimize as opt
import csv
import random
import os
import bmesh
import math
import sys
from PIL import Image, ImageFilter

# Ativando os addons necessários
# Ativando os addons necessários
addons = [
    # "bl_ext.user_default.sapling_tree_gen",
    # "bl_ext.user_default.extra_mesh_objects",
    "io_scene_gltf2",
]
for addon in addons:
    if addon not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=addon)

# Definindo cores para as árvores
trunk_colors = [
    (0.5, 0.3, 0.1, 1),  # Marrom claro
    (0.3, 0.2, 0.1, 1),  # Marrom escuro
    (0.4, 0.2, 0.1, 1),  # Marrom médio
]

leaf_colors = [
    (0.2, 0.8, 0.2, 1),  # Verde claro
    (0.1, 0.5, 0.1, 1),  # Verde escuro
    (0.3, 0.6, 0.3, 1),  # Verde médio
]

possibles_shapes = ["0", "6", "1", "2", "3", "4", "10", "5", "7"]
# Configurações das árvores
tree_presets = [
    {
        "seed": 0,
        "handleType": "0",
        "levels": 2,
        "length": (0.8, 0.6, 0.5, 0.1),
        "lengthV": (0, 0.1, 0, 0),
        "taperCrown": 0.5,
        "branches": (0, 55, 10, 1),
        "curveRes": (8, 5, 3, 1),
        "curve": (0, -15, 0, 0),
        "curveV": (20, 50, 75, 0),
        "curveBack": (0, 0, 0, 0),
        "baseSplits": 3,
        "segSplits": (0.1, 0.5, 0.2, 0),
        "splitByLen": True,
        "rMode": "rotate",
        "splitAngle": (18, 18, 22, 0),
        "splitAngleV": (5, 5, 5, 0),
        "scale": 5,
        "scaleV": 2,
        "attractUp": (3.5, -1.89984, 0, 0),
        "attractOut": (0, 0.8, 0, 0),
        "shape": random.choice(possibles_shapes),
        "shapeS": random.choice(possibles_shapes),
        "customShape": (0.5, 1, 0.3, 0.5),
        "branchDist": 1.5,
        "nrings": 0,
        "baseSize": 0.3,
        "baseSize_s": 0.16,
        "splitHeight": 0.2,
        "splitBias": 0.55,
        "ratio": 0.015,
        "minRadius": 0.0015,
        "closeTip": False,
        "rootFlare": 1,
        "autoTaper": True,
        "taper": (1, 1, 1, 1),
        "radiusTweak": (1, 1, 1, 1),
        "ratioPower": 1.2,
        "downAngle": (0, 26.21, 52.56, 30),
        "downAngleV": (0, 10, 10, 10),
        "useOldDownAngle": True,
        "useParentAngle": True,
        "rotate": (99.5, 137.5, 137.5, 137.5),
        "rotateV": (15, 0, 0, 0),
        "scale0": 1,
        "scaleV0": 0.1,
        "pruneWidth": 0.34,
        "pruneBase": 0.12,
        "pruneWidthPeak": 0.5,
        "prunePowerHigh": 0.5,
        "prunePowerLow": 0.001,
        "pruneRatio": 0.75,
        "leaves": 150,
        "leafDownAngle": 30,
        "leafDownAngleV": -10,
        "leafRotate": 137.5,
        "leafRotateV": 15,
        "leafScale": 0.4,
        "leafScaleX": 0.2,
        "leafScaleT": 0.1,
        "leafScaleV": 0.15,
        "leafShape": "hex",
        "bend": 0,
        "leafangle": -12,
        "horzLeaves": True,
        "leafDist": "6",
        "bevelRes": 1,
        "resU": 4,
        "armAnim": False,
        "previewArm": False,
        "leafAnim": False,
        "frameRate": 1,
        "loopFrames": 0,
        "wind": 1,
        "gust": 1,
        "gustF": 0.075,
        "af1": 1,
        "af2": 1,
        "af3": 4,
        "makeMesh": False,
        "armLevels": 2,
        "boneStep": (1, 1, 1, 1),
    },
    {
        "seed": 2,
        "handleType": "0",
        "levels": 3,
        "length": (1.2, 0.8, 0.5, 0.2),
        "lengthV": (0.1, 0.2, 0.1, 0.1),
        "taperCrown": 0.7,
        "branches": (0, 30, 20, 5),
        "curveRes": (6, 5, 4, 2),
        "curve": (5, -10, 5, 0),
        "curveV": (10, 30, 60, 0),
        "curveBack": (0, 0, 0, 0),
        "baseSplits": 1,
        "segSplits": (0.2, 0.3, 0.4, 0.1),
        "splitByLen": True,
        "rMode": "rotate",
        "splitAngle": (15, 10, 20, 5),
        "splitAngleV": (3, 4, 5, 1),
        "scale": 7,
        "scaleV": 4,
        "attractUp": (5.0, -2.0, 0, 0),
        "attractOut": (0, 1.2, 0, 0),
        "shape": random.choice(possibles_shapes),
        "shapeS": random.choice(possibles_shapes),
        "customShape": (0.7, 1.5, 0.5, 0.7),
        "branchDist": 1.3,
        "nrings": 2,
        "baseSize": 0.5,
        "baseSize_s": 0.2,
        "splitHeight": 0.4,
        "splitBias": 0.6,
        "ratio": 0.025,
        "minRadius": 0.003,
        "closeTip": False,
        "rootFlare": 1.5,
        "autoTaper": True,
        "taper": (1, 1, 1, 1),
        "radiusTweak": (1, 1, 1, 1),
        "ratioPower": 1.3,
        "downAngle": (0, 22, 48, 20),
        "downAngleV": (0, 8, 8, 8),
        "useOldDownAngle": True,
        "useParentAngle": True,
        "rotate": (90, 130, 130, 130),
        "rotateV": (12, 0, 0, 0),
        "scale0": 1.2,
        "scaleV0": 0.3,
        "pruneWidth": 0.4,
        "pruneBase": 0.15,
        "pruneWidthPeak": 0.7,
        "prunePowerHigh": 0.7,
        "prunePowerLow": 0.003,
        "pruneRatio": 0.85,
        "leaves": 200,
        "leafDownAngle": 40,
        "leafDownAngleV": -15,
        "leafRotate": 140,
        "leafRotateV": 20,
        "leafScale": 0.5,
        "leafScaleX": 0.3,
        "leafScaleT": 0.2,
        "leafScaleV": 0.25,
        "leafShape": "hex",
        "bend": 2,
        "leafangle": -8,
        "horzLeaves": True,
        "leafDist": "6",
        "bevelRes": 1,
        "resU": 4,
        "armAnim": False,
        "previewArm": False,
        "leafAnim": False,
        "frameRate": 1,
        "loopFrames": 0,
        "wind": 1,
        "gust": 1,
        "gustF": 0.1,
        "af1": 1,
        "af2": 1,
        "af3": 4,
        "makeMesh": False,
        "armLevels": 2,
        "boneStep": (1, 1, 1, 1),
    },
    {
        "seed": 3,
        "handleType": "0",
        "levels": 4,
        "length": (1.1, 0.9, 0.6, 0.3),
        "lengthV": (0.1, 0.1, 0.2, 0.1),
        "taperCrown": 0.8,
        "branches": (0, 50, 25, 10),
        "curveRes": (9, 6, 4, 3),
        "curve": (8, -12, 6, 0),
        "curveV": (18, 40, 80, 0),
        "curveBack": (0, 0, 0, 0),
        "baseSplits": 4,
        "segSplits": (0.3, 0.6, 0.4, 0.2),
        "splitByLen": True,
        "rMode": "rotate",
        "splitAngle": (22, 20, 25, 10),
        "splitAngleV": (8, 8, 8, 4),
        "scale": 8,
        "scaleV": 4,
        "attractUp": (6.0, -2.5, 0, 0),
        "attractOut": (0, 1.5, 0, 0),
        "shape": random.choice(possibles_shapes),
        "shapeS": random.choice(possibles_shapes),
        "customShape": (0.8, 1.8, 0.6, 0.8),
        "branchDist": 1.6,
        "nrings": 3,
        "baseSize": 0.6,
        "baseSize_s": 0.25,
        "splitHeight": 0.5,
        "splitBias": 0.7,
        "ratio": 0.03,
        "minRadius": 0.004,
        "closeTip": False,
        "rootFlare": 1.8,
        "autoTaper": True,
        "taper": (1, 1, 1, 1),
        "radiusTweak": (1, 1, 1, 1),
        "ratioPower": 1.4,
        "downAngle": (0, 30, 60, 25),
        "downAngleV": (0, 12, 12, 10),
        "useOldDownAngle": True,
        "useParentAngle": True,
        "rotate": (110, 150, 150, 140),
        "rotateV": (18, 0, 0, 0),
        "scale0": 1.3,
        "scaleV0": 0.4,
        "pruneWidth": 0.45,
        "pruneBase": 0.18,
        "pruneWidthPeak": 0.75,
        "prunePowerHigh": 0.8,
        "prunePowerLow": 0.004,
        "pruneRatio": 0.9,
        "leaves": 250,
        "leafDownAngle": 45,
        "leafDownAngleV": -20,
        "leafRotate": 145,
        "leafRotateV": 25,
        "leafScale": 0.55,
        "leafScaleX": 0.35,
        "leafScaleT": 0.25,
        "leafScaleV": 0.3,
        "leafShape": "rect",
        "bend": 3,
        "leafangle": -6,
        "horzLeaves": True,
        "leafDist": "5",
        "bevelRes": 2,
        "resU": 5,
        "armAnim": False,
        "previewArm": False,
        "leafAnim": False,
        "frameRate": 1,
        "loopFrames": 0,
        "wind": 1,
        "gust": 1,
        "gustF": 0.15,
        "af1": 1,
        "af2": 1,
        "af3": 4,
        "makeMesh": False,
        "armLevels": 2,
        "boneStep": (1, 1, 1, 1),
    },
    {
        "seed": 4,
        "handleType": "1",
        "levels": 3,
        "length": (0.9, 0.7, 0.6, 0.4),
        "lengthV": (0.2, 0.1, 0.2, 0.1),
        "taperCrown": 0.6,
        "branches": (0, 45, 35, 15),
        "curveRes": (7, 5, 3, 2),
        "curve": (15, -5, 10, 0),
        "curveV": (25, 20, 40, 0),
        "curveBack": (0, 0, 0, 0),
        "baseSplits": 2,
        "segSplits": (0.3, 0.4, 0.5, 0.2),
        "splitByLen": True,
        "rMode": "rotate",
        "splitAngle": (17, 19, 27, 11),
        "splitAngleV": (4, 5, 7, 2),
        "scale": 5,
        "scaleV": 3,
        "attractUp": (4.5, -2.0, 0, 0),
        "attractOut": (0, 1.1, 0, 0),
        "shape": random.choice(possibles_shapes),
        "shapeS": random.choice(possibles_shapes),
        "customShape": (0.4, 0.8, 0.5, 0.6),
        "branchDist": 1.2,
        "nrings": 1,
        "baseSize": 0.4,
        "baseSize_s": 0.15,
        "splitHeight": 0.3,
        "splitBias": 0.5,
        "ratio": 0.02,
        "minRadius": 0.002,
        "closeTip": False,
        "rootFlare": 1.2,
        "autoTaper": True,
        "taper": (1, 1, 1, 1),
        "radiusTweak": (1, 1, 1, 1),
        "ratioPower": 1.1,
        "downAngle": (0, 24, 48, 22),
        "downAngleV": (0, 9, 11, 7),
        "useOldDownAngle": True,
        "useParentAngle": True,
        "rotate": (105, 130, 125, 120),
        "rotateV": (14, 0, 0, 0),
        "scale0": 1.2,
        "scaleV0": 0.2,
        "pruneWidth": 0.36,
        "pruneBase": 0.14,
        "pruneWidthPeak": 0.6,
        "prunePowerHigh": 0.6,
        "prunePowerLow": 0.002,
        "pruneRatio": 0.8,
        "leaves": 180,
        "leafDownAngle": 35,
        "leafDownAngleV": -12,
        "leafRotate": 135.5,
        "leafRotateV": 17,
        "leafScale": 0.45,
        "leafScaleX": 0.25,
        "leafScaleT": 0.15,
        "leafScaleV": 0.2,
        "leafShape": "hex",
        "bend": 1,
        "leafangle": -10,
        "horzLeaves": True,
        "leafDist": "6",
        "bevelRes": 1,
        "resU": 4,
        "armAnim": False,
        "previewArm": False,
        "leafAnim": False,
        "frameRate": 1,
        "loopFrames": 0,
        "wind": 1,
        "gust": 1,
        "gustF": 0.1,
        "af1": 1,
        "af2": 1,
        "af3": 4,
        "makeMesh": False,
        "armLevels": 2,
        "boneStep": (1, 1, 1, 1),
    },
    {
        "seed": 5,
        "handleType": "1",
        "levels": 3,
        "length": (0.9, 0.7, 0.5, 0.2),
        "lengthV": (0.1, 0.1, 0.1, 0.1),
        "taperCrown": 0.65,
        "branches": (0, 40, 25, 8),
        "curveRes": (7, 5, 3, 1),
        "curve": (10, -8, 10, 0),
        "curveV": (15, 25, 60, 0),
        "curveBack": (0, 0, 0, 0),
        "baseSplits": 3,
        "segSplits": (0.15, 0.35, 0.25, 0.05),
        "splitByLen": True,
        "rMode": "rotate",
        "splitAngle": (20, 15, 25, 8),
        "splitAngleV": (5, 5, 5, 2),
        "scale": 6,
        "scaleV": 3,
        "attractUp": (4.0, -1.5, 0, 0),
        "attractOut": (0, 1.0, 0, 0),
        "shape": random.choice(possibles_shapes),  # Correção aqui
        "shapeS": random.choice(possibles_shapes),
        "customShape": (0.6, 1.0, 0.4, 0.5),
        "branchDist": 1.4,
        "nrings": 1,
        "baseSize": 0.35,
        "baseSize_s": 0.18,
        "splitHeight": 0.35,
        "splitBias": 0.6,
        "ratio": 0.02,
        "minRadius": 0.002,
        "closeTip": False,
        "rootFlare": 1.3,
        "autoTaper": True,
        "taper": (1, 1, 1, 1),
        "radiusTweak": (1, 1, 1, 1),
        "ratioPower": 1.2,
        "downAngle": (0, 24, 50, 20),
        "downAngleV": (0, 10, 10, 10),
        "useOldDownAngle": True,
        "useParentAngle": True,
        "rotate": (95, 135, 135, 135),
        "rotateV": (12, 0, 0, 0),
        "scale0": 1.1,
        "scaleV0": 0.2,
        "pruneWidth": 0.38,
        "pruneBase": 0.16,
        "pruneWidthPeak": 0.65,
        "prunePowerHigh": 0.65,
        "prunePowerLow": 0.002,
        "pruneRatio": 0.78,
        "leaves": 160,
        "leafDownAngle": 38,
        "leafDownAngleV": -10,
        "leafRotate": 136,
        "leafRotateV": 18,
        "leafScale": 0.42,
        "leafScaleX": 0.22,
        "leafScaleT": 0.12,
        "leafScaleV": 0.18,
        "leafShape": "rect",
        "bend": 1,
        "leafangle": -11,
        "horzLeaves": True,
        "leafDist": "6",
        "bevelRes": 1,
        "resU": 4,
        "armAnim": False,
        "previewArm": False,
        "leafAnim": False,
        "frameRate": 1,
        "loopFrames": 0,
        "wind": 1,
        "gust": 1,
        "gustF": 0.08,
        "af1": 1,
        "af2": 1,
        "af3": 4,
        "makeMesh": False,
        "armLevels": 2,
        "boneStep": (1, 1, 1, 1),
    },
    {
        "seed": 6,
        "handleType": "1",
        "levels": 4,
        "length": (1.0, 0.8, 0.6, 0.3),
        "lengthV": (0.2, 0.1, 0.2, 0.1),
        "taperCrown": 0.75,
        "branches": (0, 60, 40, 12),
        "curveRes": (8, 6, 4, 2),
        "curve": (12, -15, 12, 0),
        "curveV": (20, 35, 70, 0),
        "curveBack": (0, 0, 0, 0),
        "baseSplits": 2,
        "segSplits": (0.25, 0.4, 0.35, 0.15),
        "splitByLen": True,
        "rMode": "rotate",
        "splitAngle": (18, 18, 22, 7),
        "splitAngleV": (6, 6, 6, 3),
        "scale": 7,
        "scaleV": 4,
        "attractUp": (5.5, -1.8, 0, 0),
        "attractOut": (0, 1.3, 0, 0),
        "shape": random.choice(possibles_shapes),  # Correção aqui
        "shapeS": random.choice(possibles_shapes),
        "customShape": (0.7, 1.3, 0.6, 0.7),
        "branchDist": 1.6,
        "nrings": 2,
        "baseSize": 0.45,
        "baseSize_s": 0.22,
        "splitHeight": 0.4,
        "splitBias": 0.65,
        "ratio": 0.025,
        "minRadius": 0.0025,
        "closeTip": False,
        "rootFlare": 1.4,
        "autoTaper": True,
        "taper": (1, 1, 1, 1),
        "radiusTweak": (1, 1, 1, 1),
        "ratioPower": 1.3,
        "downAngle": (0, 28, 54, 23),
        "downAngleV": (0, 11, 11, 9),
        "useOldDownAngle": True,
        "useParentAngle": True,
        "rotate": (100, 140, 140, 140),
        "rotateV": (15, 0, 0, 0),
        "scale0": 1.15,
        "scaleV0": 0.3,
        "pruneWidth": 0.42,
        "pruneBase": 0.15,
        "pruneWidthPeak": 0.68,
        "prunePowerHigh": 0.68,
        "prunePowerLow": 0.002,
        "pruneRatio": 0.82,
        "leaves": 190,
        "leafDownAngle": 42,
        "leafDownAngleV": -12,
        "leafRotate": 138,
        "leafRotateV": 17,
        "leafScale": 0.48,
        "leafScaleX": 0.28,
        "leafScaleT": 0.15,
        "leafScaleV": 0.22,
        "leafShape": "hex",
        "bend": 2,
        "leafangle": -9,
        "horzLeaves": True,
        "leafDist": "6",
        "bevelRes": 1,
        "resU": 4,
        "armAnim": False,
        "previewArm": False,
        "leafAnim": False,
        "frameRate": 1,
        "loopFrames": 0,
        "wind": 1,
        "gust": 1,
        "gustF": 0.12,
        "af1": 1,
        "af2": 1,
        "af3": 4,
        "makeMesh": False,
        "armLevels": 2,
        "boneStep": (1, 1, 1, 1),
    },
    {
        "seed": 7,
        "handleType": "1",
        "levels": 2,
        "length": (1.1, 0.9, 0.7, 0.4),
        "lengthV": (0.15, 0.1, 0.15, 0.1),
        "taperCrown": 0.7,
        "branches": (0, 35, 30, 10),
        "curveRes": (7, 5, 3, 2),
        "curve": (10, -10, 10, 0),
        "curveV": (18, 30, 50, 0),
        "curveBack": (0, 0, 0, 0),
        "baseSplits": 2,
        "segSplits": (0.2, 0.3, 0.4, 0.1),
        "splitByLen": True,
        "rMode": "rotate",
        "splitAngle": (17, 14, 24, 9),
        "splitAngleV": (4, 4, 4, 2),
        "scale": 6,
        "scaleV": 3,
        "attractUp": (4.5, -1.5, 0, 0),
        "attractOut": (0, 1.1, 0, 0),
        "shape": random.choice(possibles_shapes),  # Correção aqui
        "shapeS": random.choice(possibles_shapes),
        "customShape": (0.5, 1.2, 0.4, 0.6),
        "branchDist": 1.3,
        "nrings": 2,
        "baseSize": 0.4,
        "baseSize_s": 0.2,
        "splitHeight": 0.3,
        "splitBias": 0.55,
        "ratio": 0.022,
        "minRadius": 0.002,
        "closeTip": False,
        "rootFlare": 1.2,
        "autoTaper": True,
        "taper": (1, 1, 1, 1),
        "radiusTweak": (1, 1, 1, 1),
        "ratioPower": 1.2,
        "downAngle": (0, 26, 52, 22),
        "downAngleV": (0, 10, 10, 8),
        "useOldDownAngle": True,
        "useParentAngle": True,
        "rotate": (98, 135, 135, 135),
        "rotateV": (13, 0, 0, 0),
        "scale0": 1.2,
        "scaleV0": 0.25,
        "pruneWidth": 0.36,
        "pruneBase": 0.13,
        "pruneWidthPeak": 0.64,
        "prunePowerHigh": 0.64,
        "prunePowerLow": 0.003,
        "pruneRatio": 0.8,
        "leaves": 170,
        "leafDownAngle": 36,
        "leafDownAngleV": -11,
        "leafRotate": 137,
        "leafRotateV": 16,
        "leafScale": 0.46,
        "leafScaleX": 0.26,
        "leafScaleT": 0.13,
        "leafScaleV": 0.19,
        "leafShape": "rect",
        "bend": 1,
        "leafangle": -10,
        "horzLeaves": True,
        "leafDist": "6",
        "bevelRes": 1,
        "resU": 4,
        "armAnim": False,
        "previewArm": False,
        "leafAnim": False,
        "frameRate": 1,
        "loopFrames": 0,
        "wind": 1,
        "gust": 1,
        "gustF": 0.1,
        "af1": 1,
        "af2": 1,
        "af3": 4,
        "makeMesh": False,
        "armLevels": 2,
        "boneStep": (1, 1, 1, 1),
    },
]


# Função para criar um plano manualmente
def create_manual_plane(size):
    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new(name="ManualPlane")
    obj = bpy.data.objects.new("ManualPlane", mesh)

    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    vertices = [
        (-size / 2, -size / 2, 0),
        (size / 2, -size / 2, 0),
        (size / 2, size / 2, 0),
        (-size / 2, size / 2, 0),
    ]

    edges = []
    faces = [(0, 1, 2, 3)]

    mesh.from_pydata(vertices, edges, faces)
    mesh.update()

    return obj


# Função para subdividir um objeto
def subdivide_object(obj, cuts):
    if obj:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.subdivide(number_cuts=cuts)
        bpy.ops.object.mode_set(mode="OBJECT")
    else:
        print("Objeto não encontrado.")


# Função para criar árvores
def get_terrain_z(x, y, terrain):
    # Cria um vetor de origem e direção para o ray cast
    origin = Vector((x, y, terrain.location.z + terrain.dimensions.z + 10))
    direction = Vector((0, 0, -1))
    # Executa o ray cast
    result, location, normal, face_index = terrain.ray_cast(origin, direction)
    if result:
        return location.z

    # Alternativa: encontrar a altura manualmente se o ray casting falhar
    mesh = terrain.data
    vertices = [terrain.matrix_world @ vert.co for vert in mesh.vertices]
    faces = [face.vertices for face in mesh.polygons]

    for face in faces:
        verts = [vertices[idx] for idx in face]
        if is_point_in_triangle((x, y), verts):
            z = interpolate_z((x, y), verts)
            return z
    return 0  # Default Z if ray cast fails


def is_point_in_triangle(pt, verts):
    x, y = pt
    x1, y1, _ = verts[0]
    x2, y2, _ = verts[1]
    x3, y3, _ = verts[2]

    # Barycentric coordinates
    det = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    l1 = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / det
    l2 = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / det
    l3 = 1 - l1 - l2

    return l1 >= 0 and l2 >= 0 and l3 >= 0


def interpolate_z(pt, verts):
    x, y = pt
    x1, y1, z1 = verts[0]
    x2, y2, z2 = verts[1]
    x3, y3, z3 = verts[2]

    det = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    l1 = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / det
    l2 = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / det
    l3 = 1 - l1 - l2

    return l1 * z1 + l2 * z2 + l3 * z3


def create_trees(
    num_trees, terrain=None, points=None, tree_presets=None, add_leaves=True
):
    if tree_presets is None:
        tree_presets = [{}]  # Default empty preset

    used_positions = set()

    if terrain:
        min_x = terrain.location.x - terrain.dimensions.x / 2
        max_x = terrain.location.x + terrain.dimensions.x / 2
        min_y = terrain.location.y - terrain.dimensions.y / 2
        max_y = terrain.location.y + terrain.dimensions.y / 2
    else:
        min_x = -10
        max_x = 10
        min_y = -10
        max_y = 10

    def generate_unique_position():
        while True:
            if points is not None:
                idx = random.randint(0, len(points) - 1)
                x, y, z = points[idx]
                position_tuple = (x, y)
                if position_tuple not in used_positions:
                    used_positions.add(position_tuple)
                    return x, y, z
            else:
                x = random.uniform(min_x, max_x)
                y = random.uniform(min_y, max_y)
                position_tuple = (x, y)
                if position_tuple not in used_positions:
                    used_positions.add(position_tuple)
                    return x, y, get_terrain_z(x, y, terrain)

    created_trees = []
    for _ in range(num_trees):
        x, y, z = generate_unique_position()
        tree_preset = random.choice(
            tree_presets
        )  # Escolher um preset de árvore aleatoriamente
        bpy.ops.object.select_all(action="DESELECT")

        # Obter a lista de objetos antes de adicionar a árvore
        objects_before = set(bpy.data.objects)

        result = bpy.ops.curve.tree_add(
            do_update=True,
            bevel=True,
            prune=False,
            showLeaves=add_leaves,
            **tree_preset,
        )
        print(f"Tree creation result: {result}")

        # Obter a lista de objetos depois de adicionar a árvore
        objects_after = set(bpy.data.objects)

        # Encontrar o novo objeto
        new_objects = objects_after - objects_before
        if new_objects:
            new_objects_list = list(new_objects)
            for obj in new_objects_list:
                if (
                    obj.type == "CURVE" and "leaf" not in obj.name.lower()
                ):  # Garantir que é uma árvore e não apenas folhas
                    tree = obj
                    bpy.context.view_layer.objects.active = tree
                    tree.select_set(True)
                    tree.location = (x, y, z)
                    tree.scale = (0.3, 0.3, 0.3)
                    created_trees.append(tree)
                    print(
                        f"Tree created at location: ({x}, {y}, {z}) with preset {tree_preset['seed']}"
                    )
                    break
        else:
            print("No new tree object created")
    return created_trees


def create_tree_at_position(x, y, z, height, tree_preset=None, add_leaves=True):
    if tree_preset is None:
        tree_preset = {}  # Default empty preset

    bpy.ops.object.select_all(action="DESELECT")

    # Obter a lista de objetos antes de adicionar a árvore
    objects_before = set(bpy.data.objects)

    result = bpy.ops.curve.tree_add(
        do_update=True,
        bevel=True,
        prune=False,
        showLeaves=add_leaves,
        **tree_preset,
    )
    print(f"Tree creation result: {result}")

    # Obter a lista de objetos depois de adicionar a árvore
    objects_after = set(bpy.data.objects)

    # Encontrar o novo objeto
    new_objects = objects_after - objects_before
    if new_objects:
        new_objects_list = list(new_objects)
        for obj in new_objects_list:
            if (
                obj.type == "CURVE" and "leaf" not in obj.name.lower()
            ):  # Garantir que é uma árvore e não apenas folhas
                tree = obj
                bpy.context.view_layer.objects.active = tree
                tree.select_set(True)
                tree.location = (x, y, z)
                tree.scale = (height, height, height)
                print(
                    f"Tree created at location: ({x}, {y}, {z}) with height {height} and preset {tree_preset.get('seed', 'default')}"
                )
                return tree
    else:
        print("No new tree object created")
    return None


def get_external_material(material_file_path, material_name):
    # Anexa o material do arquivo externo do Blender
    with bpy.data.libraries.load(material_file_path, link=False) as (
        data_from,
        data_to,
    ):
        if material_name in data_from.materials:
            data_to.materials = [material_name]

    # Obtem o material anexado
    material = bpy.data.materials.get(material_name)

    return material


# Função para criar materiais de cores diferentes
def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    return mat


# Função para aplicar materiais de forma detalhada
def apply_material_recursive(obj, trunk_mat, leaf_mat, level=0):
    indent = " " * (level * 2)
    print(f"{indent}Acessando objeto {obj.name}, tipo: {obj.type}")

    if "leaves" in obj.name.lower() or "Leaves" in obj.data.name:
        if obj.data and obj.data.materials:
            obj.data.materials[0] = leaf_mat
            print(f"{indent}Material {leaf_mat.name} aplicado a {obj.name}")
        else:
            obj.data.materials.append(leaf_mat)
            print(f"{indent}Material {leaf_mat.name} adicionado a {obj.name}")
    elif "tree" in obj.name.lower() or "Tree" in obj.data.name:
        if obj.data and obj.data.materials:
            obj.data.materials[0] = trunk_mat
            print(f"{indent}Material {trunk_mat.name} aplicado a {obj.name}")
        else:
            obj.data.materials.append(trunk_mat)
            print(f"{indent}Material {trunk_mat.name} adicionado a {obj.name}")

    for child in obj.children:
        apply_material_recursive(child, trunk_mat, leaf_mat, level + 1)


# Função para aplicar cores às árvores e folhas
def apply_tree_colors(trees, trunk_colors, leaf_colors):
    trunk_materials = [
        create_material(f"TrunkMaterial{i}", color)
        for i, color in enumerate(trunk_colors)
    ]
    leaf_materials = [
        create_material(f"LeafMaterial{i}", color)
        for i, color in enumerate(leaf_colors)
    ]

    for tree in trees:
        trunk_mat = random.choice(trunk_materials)
        leaf_mat = random.choice(leaf_materials)

        # Aplicando materiais de forma recursiva
        apply_material_recursive(tree, trunk_mat, leaf_mat)

    # Aplicar materiais às folhas que não estão nos níveis mais altos
    for obj in bpy.data.objects:
        if obj.type == "MESH" and "leaves" in obj.name.lower():
            leaf_mat = random.choice(leaf_materials)
            if obj.data and obj.data.materials:
                obj.data.materials[0] = leaf_mat
                print(f"Material {leaf_mat.name} aplicado a {obj.name}")
            else:
                obj.data.materials.append(leaf_mat)
                print(f"Material {leaf_mat.name} adicionado a {obj.name}")


# Função para criar materiais para os arbustos
def create_bush_materials(num_materials):
    bush_materials = []
    for i in range(num_materials):
        color = (
            random.uniform(0, 1),
            random.uniform(0.5, 1),
            random.uniform(0, 0.5),
            1,
        )
        mat = create_material(f"BushMaterial{i}", color)
        bush_materials.append(mat)
    return bush_materials


def create_bushes(num_bushes, terrain=None, points=None):
    used_positions = set()

    if terrain:
        min_x = terrain.location.x - terrain.dimensions.x / 2
        max_x = terrain.location.x + terrain.dimensions.x / 2
        min_y = terrain.location.y - terrain.dimensions.y / 2
        max_y = terrain.location.y + terrain.dimensions.y / 2
    else:
        min_x = -10
        max_x = 10
        min_y = -10
        max_y = 10

    def generate_unique_position():
        while True:
            if points is not None:
                idx = random.randint(0, len(points) - 1)
                x, y, z = points[idx]
                position_tuple = (x, y)
                if position_tuple not in used_positions:
                    used_positions.add(position_tuple)
                    return x, y, z
            else:
                x = random.uniform(min_x, max_x)
                y = random.uniform(min_y, max_y)
                position_tuple = (x, y)
                if position_tuple not in used_positions:
                    used_positions.add(position_tuple)
                    return x, y, get_terrain_z(x, y, terrain)

    bush_materials = create_bush_materials(num_bushes)
    for _ in range(num_bushes):
        x, y, z = generate_unique_position()
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.5)
        bush = bpy.context.object
        if bush:
            bush.location = (x, y, z)
            bush.scale = (0.5, 0.5, 0.5)
            bush.data.materials.append(random.choice(bush_materials))
            print(f"Bush created at location: ({x}, {y}, {z})")


# Função para criar grama
def create_grass(terrain):
    if terrain:
        bpy.context.view_layer.objects.active = terrain
        bpy.ops.object.particle_system_add()
        psys = terrain.particle_systems[-1]
        psys.name = "Grass"
        psys.settings.type = "HAIR"
        psys.settings.count = 10000
        psys.settings.hair_length = 0.3
        psys.settings.emit_from = "FACE"
        psys.settings.render_type = "PATH"

        grass_material = bpy.data.materials.new(name="GrassMaterial")
        grass_material.use_nodes = True
        bsdf = grass_material.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (0, 1, 0, 1)
        # terrain.data.materials.append(grass_material)

        psys.settings.material = len(terrain.data.materials)
        print("Grass created on terrain")


# =================================================================================================================


def read_csv_data(filepath):
    coords = []
    front_coords = []
    colors = []
    road_coords = []

    with open(filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                x = float(row["x"])
                y = float(row["y"])
                z = float(row["z"])
                front = int(row["front"])
                road = int(row["road"])
                color = str(row["hex_color"])

                if road != 1:
                    coords.append((x, y, z))
                if front == 1:
                    front_coords.append((x, y, z))
                if road == 1:
                    road_coords.append((x, y, z))
                colors.append(color)
            except ValueError:
                # Ignorar linhas com valores inválidos
                pass

    # Normalizar as coordenadas subtraindo os valores mínimos
    min_x = min(coord[0] for coord in coords)
    min_y = min(coord[1] for coord in coords)
    min_z = min(coord[2] for coord in coords)
    normalized_coords = [
        (x - min_x, y - min_y, z - min_z) for x, y, z in coords
    ]
    normalized_front_coords = [
        (x - min_x, y - min_y, z - min_z) for x, y, z in front_coords
    ]
    normalized_road_coords = [
        (x - min_x, y - min_y, z - min_z) for x, y, z in road_coords
    ]

    normalized_road_coords = list(
        set(normalized_road_coords)
    )  # Remove points with duplicate values
    # normalized_road_coords = [(x, y, 0) for x, y, z in normalized_road_coords]

    return (
        np.array(normalized_coords),
        normalized_front_coords,
        colors,
        normalized_road_coords,
    )


def find_convex_hull(points):
    # Utilizar a função ConvexHull da biblioteca scipy.spatial para encontrar a casca convexa
    hull = ConvexHull(
        points[:, :2]
    )  # Usar apenas X e Y para encontrar a casca convexa
    hull_points = points[hull.vertices]
    return hull_points


def generate_random_points(num_points=100):
    # Gerar pontos X e Y aleatórios entre 0 e 100
    points = np.random.rand(num_points, 2) * 100

    # Calcular Z como uma variação de 10% a 30% para mais ou para menos
    z_base = np.random.rand(num_points) * 15
    z_variation = (
        z_base
        * (0.1 + 0.2 * np.random.rand(num_points))
        * (np.random.choice([-1, 1], num_points))
    )
    z = z_base + z_variation

    # Combinar X, Y e Z em um array de pontos
    points_3d = np.column_stack((points, z))
    return points_3d


def project_to_xy(points, min_z):
    # Projeta os pontos da casca convexa no plano XY usando o menor valor de Z
    projected_points = points.copy()
    projected_points[:, 2] = min_z
    return projected_points


def find_lateral_faces(hull_points, projected_points):
    faces = []
    num_points = len(hull_points)

    for i in range(num_points):
        next_i = (i + 1) % num_points
        face = [
            hull_points[i],
            hull_points[next_i],
            projected_points[next_i],
            projected_points[i],
        ]
        faces.append(face)

    return faces


def get_faces_indices(points, faces):
    indices = []
    for face in faces:
        indices.append(
            [
                np.where(np.all(points == face[0], axis=1))[0][0],
                np.where(np.all(points == face[1], axis=1))[0][0],
                np.where(np.all(points == face[2], axis=1))[0][0],
                np.where(np.all(points == face[3], axis=1))[0][0],
            ]
        )
    return indices


# def create_lateral_mesh(points, faces_indices):
#     # Nome da malha e do objeto
#     mesh_name = "ConvexHullMesh"
#     object_name = "ConvexHullObject"

#     # Criar uma nova malha e um novo objeto
#     mesh = bpy.data.meshes.new(mesh_name)
#     obj = bpy.data.objects.new(object_name, mesh)

#     # Adicionar o objeto na cena
#     bpy.context.collection.objects.link(obj)

#     # Set the object as active and select it
#     bpy.context.view_layer.objects.active = obj
#     obj.select_set(True)

#     # Convert the points to a list of tuples (vertices)
#     vertices = [tuple(point) for point in points]

#     # Criar a malha a partir dos vértices e faces
#     mesh.from_pydata(vertices, [], faces_indices)

#     # Adiciona uma layer de vertex color
#     if not mesh.vertex_colors:
#         mesh.vertex_colors.new()

#     color_layer = mesh.vertex_colors.active

#     # Pinta os todos os vertices de vermelho
#     for poly in mesh.polygons:
#         for loop_index in poly.loop_indices:
#             color_layer.data[loop_index].color = (1.0, 0.0, 0.0, 1.0) # VERMELHO

#     # Atualizar a malha com a nova geometria
#     mesh.update()

#     # Garante que estamos no modo edit
#     bpy.ops.object.mode_set(mode='EDIT')

#     # Seleciona todos os vertices
#     bpy.ops.mesh.select_all(action='SELECT')

#     # Junta os vertices que estiverem muito proximos.
#     # bpy.ops.mesh.remove_doubles()

#     bpy.ops.mesh.normals_make_consistent()

#     bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

#     # Volta para o modo Objeto
#     bpy.ops.object.mode_set(mode='OBJECT')

#     bpy.ops.object.select_all(action='DESELECT')

#     return obj


# Função para combinar pontos originais e projetados
def combine_points_and_projected(hull_points, projected_points):
    return np.vstack((hull_points, projected_points))


def create_base(projected_points):
    # Nome da malha e do objeto
    base_mesh_name = "BaseMesh"
    base_object_name = "BaseObject"

    # Criar uma nova malha e um novo objeto
    base_mesh = bpy.data.meshes.new(base_mesh_name)
    base_obj = bpy.data.objects.new(base_object_name, base_mesh)

    # Adicionar o objeto na cena
    bpy.context.collection.objects.link(base_obj)

    # Set the object as active and select it
    bpy.context.view_layer.objects.active = base_obj
    base_obj.select_set(True)

    # Convert the points to a list of tuples (vertices)
    projected_points = [(x, y, 0) for x, y, z in projected_points]
    vertices = [tuple(point) for point in projected_points]

    # Criar a face a partir dos vértices
    faces = [list(range(len(vertices)))]

    # Criar a malha a partir dos vértices e faces
    base_mesh.from_pydata(vertices, [], faces)

    # Adiciona uma layer de vertex color
    if not base_mesh.vertex_colors:
        base_mesh.vertex_colors.new()

    color_layer = base_mesh.vertex_colors.active

    # Pinta os todos os vertices de verde
    for poly in base_mesh.polygons:
        for loop_index in poly.loop_indices:
            color_layer.data[loop_index].color = (
                1.0,
                0.0,
                0.0,
                1.0,
            )  # VERMELHO

    # Atualizar a malha com a nova geometria
    base_mesh.update()

    # Garante que estamos no modo edit
    bpy.ops.object.mode_set(mode="EDIT")

    # Seleciona todos os vertices
    bpy.ops.mesh.select_all(action="SELECT")

    # Junta os vertices que estiverem muito proximos.
    bpy.ops.mesh.remove_doubles()

    bpy.ops.mesh.normals_make_consistent(inside=True)

    bpy.ops.mesh.quads_convert_to_tris(
        quad_method="BEAUTY", ngon_method="BEAUTY"
    )

    # Volta para o modo Objeto
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")

    return base_obj


def delaunay_triangulation(points):
    # Fazer a triangulação de Delaunay
    tri = Delaunay(points[:, :2])  # Usar apenas X e Y para a triangulação
    return tri.simplices


def create_surface_faces(vertices, faces_indices, colors):
    # Cria uma nova malha e um novo objeto
    mesh = bpy.data.meshes.new(name="Terrain")
    obj = bpy.data.objects.new(name="Terrain", object_data=mesh)

    # Adiciona o objeto ao contexto da cena
    bpy.context.collection.objects.link(obj)

    # Cria a malha a partir dos vértices e faces
    mesh.from_pydata(vertices, [], faces_indices)

    # Adiciona uma layer de vertex color
    if not mesh.vertex_colors:
        mesh.vertex_colors.new()

    color_layer = mesh.vertex_colors.active

    # Pinta os vertices com as cores do terreno
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_vert_index = mesh.loops[loop_index].vertex_index
            color_layer.data[loop_index].color = hex_to_rgba(
                colors[loop_vert_index]
            )

    mesh.update()

    print(
        f"Criado um terreno com {len(vertices)} pontos e {len(faces_indices)} faces."
    )
    return obj


def perpendicular_vector(v):
    # Encontra um vetor perpendicular arbitrário no espaço 3D
    if v[0] != 0 or v[1] != 0:
        return np.array([-v[1], v[0], 0])
    else:
        return np.array([1, 0, -v[2] / v[0]])


def project_points_on_parallel_line(p, a, b, offset=4.5):
    # Calcula o vetor direção
    d = np.array(b) - np.array(a)

    # Vetor do ponto A até o ponto a ser projetado
    a_p = np.array(p) - np.array(a)

    # Projeção vetorial
    proj = (np.dot(a_p, d) / np.dot(d, d)) * d

    # Ponto projetado
    projected_point = np.array(a) + proj

    # Vetor perpendicular
    u = perpendicular_vector(d)
    u = u / np.linalg.norm(u)  # Normaliza o vetor perpendicular

    # Adiciona o offset para criar a reta paralela
    point_with_offset = projected_point + offset * u

    return point_with_offset


def project_road_on_front_points(farthest_vertex, left_dir, offset=0.0):
    new_points = []
    for point in road_line_points:
        point = project_points_on_parallel_line(
            point, farthest_vertex, Vector(farthest_vertex) + left_dir, offset
        )
        new_points.append(tuple(point))
    return new_points


def move_points(list_A, list_B, direction_vector, offset=4.5):
    list_A = np.array(list_A)
    list_B = np.array(list_B)
    direction_vector = np.array(direction_vector) / np.linalg.norm(
        direction_vector
    )  # Normalizar o vetor de direção

    result = []

    for point_B in list_B:
        found = False
        for point_A in list_A:
            movement_vector = point_A - point_B
            specific_direction = (
                movement_vector.dot(direction_vector) * direction_vector
            )

            if np.allclose(specific_direction, movement_vector, atol=1e-2):
                # Adicionar o offset na direção especificada, mas apenas para os eixos X e Y
                offset_vector = offset * direction_vector
                offset_vector[2] = 0  # Zerar o componente Z do offset

                new_point = point_B + specific_direction + offset_vector
                result.append(tuple(new_point))
                found = True
                break
        if not found:
            # Mover o ponto com o offset na direção especificada mesmo que nenhum ponto seja encontrado dentro do raio
            offset_vector = offset * direction_vector
            offset_vector[2] = 0  # Zerar o componente Z do offset

            new_point = point_B + offset_vector
            result.append(tuple(new_point))

    return result


def smooth_objects(objects):
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")

    for object in objects:
        object.select_set(True)

    bpy.context.view_layer.objects.active = objects[0]

    bpy.ops.object.shade_smooth()

    bpy.ops.object.select_all(action="DESELECT")


def normalize_vertices_to_zero(objects):
    for obj in objects:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

        # Select the object
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # Iterate over each vertex and move those below Z=0 to Z=0
        for vertex in obj.data.vertices:
            if vertex.co.z < 0:
                vertex.co.z = 0

        # Update the mesh
        obj.data.update()

        # Garante que estamos no modo edit
        bpy.ops.object.mode_set(mode="EDIT")

        # Seleciona todos os vertices
        bpy.ops.mesh.select_all(action="SELECT")

        # Junta os vertices que estiverem muito proximos.
        # bpy.ops.mesh.remove_doubles()

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")


def move_vertices_to_zero(obj, vertices):
    # Certifique-se de que o objeto está no modo de objeto
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")

    # Definir o objeto ativo
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Alternar para o modo de edição
    bpy.ops.object.mode_set(mode="EDIT")

    # Obter a malha bmesh para acesso mais fácil aos vértices
    bm = bmesh.from_edit_mesh(obj.data)

    # Iterar pelos vértices e mover aqueles especificados
    for v in bm.verts:
        if v.index in vertices:
            # Converter a coordenada local do vértice para a coordenada mundial
            world_coord = obj.matrix_world @ v.co
            # Definir a coordenada z mundial para zero
            world_coord.z = 0
            # Converter de volta para a coordenada local
            v.co = obj.matrix_world.inverted() @ world_coord

    # Atualizar a malha bmesh e alternar de volta para o modo de objeto
    bmesh.update_edit_mesh(obj.data)
    bm.free()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")

    # print(f"Vértices {vertices} movidos para z=0 no espaço mundial.")


def load_image(image_path):
    # Carrega a imagem
    img = bpy.data.images.load(image_path)
    return img


def create_texture(image, texture_name="TerrainTexture"):
    # Cria uma nova textura
    tex = bpy.data.textures.new(name=texture_name, type="IMAGE")
    tex.image = image
    return tex


def assign_texture(obj, image, texture_name="TerrainTexture"):
    # Cria um novo material
    mat = bpy.data.materials.new(name=f"{texture_name}Material")
    mat.use_nodes = True

    # Limpa os nós existentes
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)

    # Cria novos nós
    node_texture = nodes.new(type="ShaderNodeTexImage")
    node_texture.image = image

    node_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_output = nodes.new(type="ShaderNodeOutputMaterial")

    # Conecta os nós
    links.new(node_texture.outputs["Color"], node_bsdf.inputs["Base Color"])
    links.new(node_bsdf.outputs["BSDF"], node_output.inputs["Surface"])

    # Associa o material ao objeto
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def create_uv_map(objects):
    bpy.ops.object.mode_set(mode="OBJECT")

    # Deselecionar todos objetos
    bpy.ops.object.select_all(action="DESELECT")

    # Seleciona objetos especificos por nome
    for obj in objects:
        obj.select_set(True)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    # Cria mapeamento UV
    bpy.ops.uv.smart_project(margin_method="ADD", island_margin=0.1)

    bpy.ops.object.mode_set(mode="OBJECT")


def bake_diffuse_color(objects):
    # Deselecionar todos objetos
    bpy.ops.object.select_all(action="DESELECT")

    # # Seleciona objetos especificos por nome
    for obj in objects:
        obj.select_set(True)

    # # Opcionalmente, torna um dos objetos selecionados o objeto ativo
    if objects:
        bpy.context.view_layer.objects.active = objects[0]

    # Define o mecanismo de renderização para CYCLES
    bpy.context.scene.render.engine = "CYCLES"

    # Opcionalmente, usa GPU para fazer o bake
    # -----------------------------------

    # Define o dispositivo para GPU
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = (
        "METAL"  # or 'OPTIX' for RTX cards, 'HIP' for AMD, 'ONEAPI' for Intel
    )

    # Habilita todas os dispositivos GPU disponíveis
    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    for device in bpy.context.preferences.addons["cycles"].preferences.devices:
        if device.type != "CPU":
            device.use = True

    # Define o dispositivo como GPU para a cena
    bpy.context.scene.cycles.device = "GPU"

    # -----------------------------------

    # Define a margem de bake
    bpy.context.scene.render.bake.margin = 4  # Define a margem para 4 pixels

    # Define para não limpar a imagem antes de fazer o bake
    bpy.context.scene.render.bake.use_clear = False

    # Lista para acompanhar os materiais processados
    processed_materials = []

    # Cria uma nova imagem para para fazer bake de cor difusa
    image_name = "Terrain_BaseColor"
    bpy.ops.image.new(name=image_name, width=1024, height=1024)
    base_color_image = bpy.data.images[image_name]

    # Cria uma nova imagem para para fazer bake de rugosidade
    image_name = "Terrain_Roughness"
    bpy.ops.image.new(name=image_name, width=1024, height=1024)
    roughness_image = bpy.data.images[image_name]

    # Cria uma nova imagem para para fazer bake de normal
    image_name = "Terrain_Normal"
    bpy.ops.image.new(name=image_name, width=1024, height=1024)
    normal_image = bpy.data.images[image_name]

    for obj in objects:
        if obj.type == "MESH" and obj.data.materials:
            material = obj.data.materials[0]
            if material not in processed_materials and material.use_nodes:
                processed_materials.append(material)

                nodes = material.node_tree.nodes

                for node in nodes:
                    node.select = False

                # Atribuir a imagem ao material do objeto
                diffuse_texture_node = nodes.new(type="ShaderNodeTexImage")
                diffuse_texture_node.image = base_color_image
                diffuse_texture_node.name = "base_color_image"

                # Atribui a imagem ao material do objeto
                roughness_texture_node = nodes.new(type="ShaderNodeTexImage")
                roughness_texture_node.image = roughness_image
                roughness_texture_node.name = "roughness_image"
                # roughness_texture_node.image.colorspace_settings.name = 'Non-Color'

                # Atribui a imagem ao material do objeto
                normal_texture_node = nodes.new(type="ShaderNodeTexImage")
                normal_texture_node.image = normal_image
                normal_texture_node.name = "normal_image"
                normal_texture_node.image.colorspace_settings.name = "Non-Color"

                for node in nodes:
                    node.select = False

    for obj in objects:
        if obj.type == "MESH" and obj.data.materials:
            material = obj.data.materials[0]
            if material.use_nodes:

                nodes = material.node_tree.nodes

                for node in nodes:
                    node.select = False

                # Obtém o nodo pelo nome
                selected_node = nodes.get("base_color_image")
                # Verifica se o nodo foi encontrado e então o seleciona
                if selected_node:
                    selected_node.select = True
                    material.node_tree.nodes.active = selected_node

    bpy.ops.object.bake(
        type="DIFFUSE", pass_filter={"COLOR"}, save_mode="EXTERNAL"
    )
    print("bake de diffuse")

    for obj in objects:
        if obj.type == "MESH" and obj.data.materials:
            material = obj.data.materials[0]
            if material.use_nodes:

                nodes = material.node_tree.nodes

                for node in nodes:
                    node.select = False

                # Obtém o nodo pelo nome
                selected_node = nodes.get("roughness_image")
                # Verifica se o nodo foi encontrado e então o seleciona
                if selected_node:
                    selected_node.select = True
                    material.node_tree.nodes.active = selected_node

    bpy.ops.object.bake(type="ROUGHNESS")
    print("bake de roughness")

    for obj in objects:
        if obj.type == "MESH" and obj.data.materials:
            material = obj.data.materials[0]
            if material.use_nodes:

                nodes = material.node_tree.nodes

                for node in nodes:
                    node.select = False

                # Obtém o nodo pelo nome
                selected_node = nodes.get("normal_image")
                # Verifica se o nodo foi encontrado e então o seleciona
                if selected_node:
                    selected_node.select = True
                    material.node_tree.nodes.active = selected_node

    bpy.ops.object.bake(type="NORMAL")
    print("bake de normal")

    processed_materials.clear()
    processed_materials = []

    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        if obj.type == "MESH" and obj.data.materials:
            material = obj.data.materials[0]
            if material not in processed_materials and material.use_nodes:
                processed_materials.append(material)

                nodes = material.node_tree.nodes

                for node in nodes:
                    node.select = False

                # Conecta o nó de textura à entrada de cor do shader Principled BSDF
                bsdf_node = nodes.get("Principled BSDF")
                material.node_tree.links.new(
                    nodes.get("base_color_image").outputs["Color"],
                    bsdf_node.inputs["Base Color"],
                )

                # Conecta o nó de textura à entrada de rugosidade do shader Principled BSDF
                bsdf_node = nodes.get("Principled BSDF")
                material.node_tree.links.new(
                    nodes.get("roughness_image").outputs["Color"],
                    bsdf_node.inputs["Roughness"],
                )

                # Conecta o nó de textura à entrada de normal do shader Principled BSDF
                bsdf_node = nodes.get("Principled BSDF")
                normal_map_node = nodes.new(type="ShaderNodeNormalMap")
                material.node_tree.links.new(
                    nodes.get("normal_image").outputs["Color"],
                    normal_map_node.inputs["Color"],
                )
                material.node_tree.links.new(
                    normal_map_node.outputs["Normal"],
                    bsdf_node.inputs["Normal"],
                )

                nodes.get("base_color_image").location = (0, 200)
                nodes.get("roughness_image").location = (0, -50)
                nodes.get("normal_image").location = (0, -300)
                normal_map_node.location = (150, -350)

                print(f"O objeto{obj.name} teve o material ajustado")

    bpy.ops.object.select_all(action="DESELECT")

    # Define o mecanismo de renderização para EEVEE
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"


# =================================================================================================================
def random_earthy_color():
    """Gera uma cor aleatória dentro de uma paleta de tons terrosos."""
    colors = [
        (0.545, 0.271, 0.075, 1),  # Marrom escuro
        (0.824, 0.706, 0.549, 1),  # Marrom claro
        (0.627, 0.322, 0.176, 1),  # Marrom médio
        (0.486, 0.376, 0.286, 1),  # Marrom acinzentado
        (0.596, 0.463, 0.329, 1),  # Marrom amarelado
        (0.400, 0.400, 0.120, 1),  # Verde terroso
    ]
    return random.choice(colors)


# Função para aplicar o material ao objeto
def apply_material_to_object(obj, material):
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


# --------------------------------------------
# utils


def hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return rgb + (alpha,)


def apply_blur(image_path, output_path, blur_radius=15):
    """
    Aplica o blur em uma imagem para preservar apenas as cores.

    Args:
        image_path (str): Caminho para a imagem de entrada.
        output_path (str): Caminho para salvar a imagem de saída.
        blur_radius (int): Raio do blur a ser aplicado.

    Returns:
        None
    """
    try:
        # Carrega a imagem
        image = Image.open(image_path)

        # Verifica se a imagem está em um modo suportado
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        # Aplica o Gaussian Blur
        blurred_image = image.filter(ImageFilter.GaussianBlur(blur_radius))

        # Salva a imagem resultante
        blurred_image.save(output_path)
        print(f"Imagem processada e salva em {output_path}")

        return True

    except Exception as e:
        print(f"Erro ao processar a imagem: {e}")
        return False


def setup_camera_and_light(points):
    # Verificar e remover câmeras e luzes existentes
    for obj in bpy.data.objects:
        if obj.type == "CAMERA" or obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)

    # Definir os limites da superfície
    min_x, min_y, min_z = np.min(points, axis=0)
    max_x, max_y, max_z = np.max(points, axis=0)
    center_x, center_y, center_z = (
        (min_x + max_x) / 2,
        (min_y + max_y) / 2,
        (min_z + max_z) / 2,
    )

    # Calcular a posição da câmera
    camera_distance = (
        max(max_x - min_x, max_y - min_y) * 1.5
    )  # Ajustar a distância da câmera
    camera_location = Vector(
        (
            center_x - camera_distance,
            center_y - camera_distance,
            max_z + camera_distance * 0.5,
        )
    )

    # Criar a câmera
    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.object

    # Apontar a câmera para o centro do objeto
    look_at(camera, Vector((center_x, center_y, center_z)))

    camera.data.lens = 35  # Ajustar a lente da câmera

    # Calcular a posição da luz
    light_distance = camera_distance * 0.5
    light_location = Vector(
        (
            center_x - light_distance,
            center_y - light_distance,
            max_z + light_distance * 0.5,
        )
    )

    # Criar a luz
    bpy.ops.object.light_add(type="SUN", location=light_location)
    light = bpy.context.object
    look_at(light, Vector((center_x, center_y, center_z)))
    light.data.energy = 10  # Ajustar a intensidade da luz

    # Definir a câmera como a câmera ativa da cena
    bpy.context.scene.camera = camera

    print("Câmera e luz configuradas corretamente.")


def look_at(obj, target):
    direction = target - obj.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    obj.rotation_euler = rot_quat.to_euler()


def render_scene(output_path):
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Cena renderizada e salva em {output_path}")


def disable_objects_from_render(object_names):
    for obj_name in object_names:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            obj.hide_render = True
            print(f"Objeto '{obj_name}' desativado do render.")
        else:
            print(f"Objeto '{obj_name}' não encontrado.")


def hide_objects(object_names):
    for obj_name in object_names:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            obj.hide_viewport = True  # Esconder da visualização
            print(f"Objeto '{obj_name}' escondido da cena.")
        else:
            print(f"Objeto '{obj_name}' não encontrado.")


def exclude_extra_points(line_points, front_line_points, offset):
    terrain_horizontal_distance = (
        np.linalg.norm(
            np.array(front_line_points[0])
            - np.array(front_line_points[len(front_line_points) - 1])
        )
        + offset
    )
    new_line_points = [
        line_points[0],
    ]

    for i in range(1, len(line_points)):
        current_distance = np.linalg.norm(
            np.array(line_points[0]) - np.array(line_points[i])
        )
        if current_distance < terrain_horizontal_distance:
            new_line_points.append(line_points[i])

    return new_line_points


def exclude_distant_points(front_line_points, road_midpoint, max_distance=6):
    new_points = []
    for point in front_line_points:
        current_distance = np.linalg.norm(
            np.array(point) - np.array(road_midpoint)
        )
        if current_distance < max_distance:
            new_points.append(point)

    return new_points


def euclidean_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def closest_points(points, p1, p2):
    closest_to_p1 = min(points, key=lambda point: euclidean_distance(point, p1))
    closest_to_p2 = min(points, key=lambda point: euclidean_distance(point, p2))

    def is_between(point, start, end):
        return all(
            min(s, e) <= pt <= max(s, e) for pt, s, e in zip(point, start, end)
        )

    in_between_points = [
        point
        for point in points
        if is_between(point, closest_to_p1, closest_to_p2)
    ]

    # return [closest_to_p1] + in_between_points + [closest_to_p2]
    return in_between_points


def farthest_vertex_in_direction(vertices, direction):
    # Normaliza o vetor de direção
    direction = direction / np.linalg.norm(direction)

    # Calcula o produto escalar para cada vértice
    dot_products = np.dot(vertices, direction)

    # Encontra o índice do vértice que maximiza o produto escalar
    farthest_vertex_index = np.argmax(dot_products)

    # Retorna o vértice mais distante
    farthest_vertex = vertices[farthest_vertex_index]

    return farthest_vertex


def subdivide_points(points, num_subdivisions):
    def interpolate(p1, p2, t):
        return (1 - t) * np.array(p1) + t * np.array(p2)

    subdivided_points = []

    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        subdivided_points.append(p1)

        for j in range(1, num_subdivisions + 1):
            t = j / (num_subdivisions + 1)
            new_point = interpolate(p1, p2, t)
            subdivided_points.append(tuple(new_point))

    subdivided_points.append(points[-1])
    # print(f"Subdivided points: {subdivided_points}")
    return subdivided_points


def sort_points(points, road_center, terrain_center):
    terrain_center.z = 0
    road_center.z = 0
    direction = (road_center - terrain_center).normalized()

    # print(f"O direção entre o centro do terreno e o centro da rua é {direction}")

    if not points:
        print("Nenhum vertice encontrado")
        return []

    if direction.x > 0.5:  # Facing right
        sorted_positions = sorted(points, key=lambda pos: (pos[1]))
    elif direction.x < -0.5:  # Facing left
        sorted_positions = sorted(
            points, key=lambda pos: (pos[1]), reverse=True
        )
    elif direction.y > 0.5:  # Facing right
        sorted_positions = sorted(
            points, key=lambda pos: (pos[0]), reverse=True
        )
    elif direction.y < -0.5:  # Facing left
        sorted_positions = sorted(points, key=lambda pos: (pos[0]))
    else:
        print("Não foi encontrado uma direção para fazer o alinhamento correto")
        return points

    return sorted_positions


def get_midpoint(points):
    # Separate the list into x and y coordinates
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]
    z_coords = [p[2] for p in points]

    # Get the median for each coordinate
    median_x = np.median(x_coords)
    median_y = np.median(y_coords)
    median_z = np.median(z_coords)

    median = Vector((median_x, median_y, median_z))
    print(f"O ponto medio da rua é:{median}")
    return median


# Function to find the nearest point that is not yellow
def find_nearest_non_yellow(point, colors, tree):
    distances, indices = tree.query(point, k=len(points))
    for i in range(1, len(indices)):
        if str.lower(colors[indices[i]]) != "#ffff00":
            return colors[indices[i]]
    return None


def change_yellow_points(points, colors):
    # Create a KDTree for the points
    tree = KDTree(points)

    # Change the color of yellow points
    for i, color in enumerate(colors):
        if str.lower(color) == "#ffff00":
            new_color = find_nearest_non_yellow(points[i], colors, tree)
            if new_color:
                colors[i] = new_color

    return colors


# ===========================================================================================================================
def clear_scene():
    # Seleciona todos os objetos na cena
    bpy.ops.object.select_all(action="SELECT")
    # Exclui todos os objetos selecionados
    bpy.ops.object.delete(use_global=False)
    # Limpa os dados órfãos (malhas, materiais, etc.) para liberar memória
    bpy.ops.outliner.orphans_purge(do_recursive=True)


def enable_obj_import_addon():
    if not bpy.context.preferences.addons.get("io_batch_import_objs"):
        bpy.ops.preferences.addon_enable(module="io_batch_import_objs")


def create_asphalt_material(texture_path):
    mat = bpy.data.materials.new(name="Asphalt")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Limpa todos os nós
    for node in nodes:
        nodes.remove(node)

    # Adiciona os nós necessários
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    tex_image = nodes.new(type="ShaderNodeTexImage")

    # Configura os nós
    tex_image.image = bpy.data.images.load(texture_path)
    links.new(tex_image.outputs["Color"], principled_node.inputs["Base Color"])
    links.new(principled_node.outputs["BSDF"], output_node.inputs["Surface"])

    return mat


def create_stripe_material():
    stripe_mat = bpy.data.materials.new(name="Stripe")
    stripe_mat.use_nodes = True
    nodes = stripe_mat.node_tree.nodes
    links = stripe_mat.node_tree.links

    # Limpa todos os nós
    for node in nodes:
        nodes.remove(node)

    # Adiciona os nós necessários
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")

    # Configura os nós
    principled_node.inputs["Base Color"].default_value = (1, 1, 0, 1)  # Amarelo
    links.new(principled_node.outputs["BSDF"], output_node.inputs["Surface"])

    return stripe_mat


def get_street_with_curve(blend_file_path, object_name, points, terrain):
    # Append the object
    with bpy.data.libraries.load(blend_file_path, link=False) as (
        data_from,
        data_to,
    ):
        if object_name in data_from.objects:
            data_to.objects.append(object_name)

    # Link the object to the current scene
    curve_object = bpy.data.objects[object_name]

    curve_object.location = (0, 0, 0)

    bpy.context.collection.objects.link(curve_object)

    if curve_object:
        curve_data = curve_object.data
        spline = curve_data.splines[0]

        # Check the spline type
        if spline.type == "POLY" or spline.type == "NURBS":
            # Remove existing points
            spline.points.add(len(points) - len(spline.points))

            # Update the points with new coordinates
            for i, point in enumerate(points):
                point += (1,)
                spline.points[i].co = point

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")

    curve_object.select_set(True)
    bpy.context.view_layer.objects.active = curve_object

    bpy.ops.object.modifier_add(type="SHRINKWRAP")
    bpy.ops.object.modifier_move_to_index(modifier="Shrinkwrap", index=0)
    shrinkwrap = bpy.context.object.modifiers["Shrinkwrap"]
    shrinkwrap.target = terrain
    shrinkwrap.offset = 5
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.curve.select_all(action="SELECT")

    bpy.ops.transform.resize(value=(0.995, 0.995, 0.995))
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

    new_points = []
    if curve_object:
        curve_data = curve_object.data
        spline = curve_data.splines[0]

        # Check the spline type
        if spline.type == "POLY" or spline.type == "NURBS":

            # Update the points with new coordinates
            for point in spline.points:
                new_points.append(point.co.to_3d())

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.curve.select_all(action="SELECT")

    bpy.ops.transform.resize(value=(1.100, 1.100, 1.100))

    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.convert(target="MESH")

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    bpy.ops.mesh.remove_doubles()

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")

    return curve_object, new_points


def angle_from_center(point, center):
    return math.atan2(point[1] - center[1], point[0] - center[0])


def sort_points_clockwise(points):
    # Calcula o centro dos pontos
    center = (
        sum([p[0] for p in points]) / len(points),
        sum([p[1] for p in points]) / len(points),
        sum([p[2] for p in points]) / len(points),
    )

    # Ordena os pontos com base no ângulo do centro
    sorted_points = sorted(points, key=lambda p: angle_from_center(p, center))

    return sorted_points


def create_lateral_mesh(points, name):
    # Ordena os pontos no sentido horário
    points = sort_points_clockwise(points)

    # Cria uma nova malha e objeto
    mesh = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(name=name, object_data=mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Cria um novo bmesh para construir a malha
    bm = bmesh.new()

    # Adiciona os vértices
    verts = [bm.verts.new((x, y, z)) for x, y, z in points]

    # Garante que a malha seja atualizada e conectada corretamente
    bm.verts.ensure_lookup_table()

    # Cria as arestas entre os vértices na ordem dada
    for i in range(len(verts)):
        bm.edges.new((verts[i], verts[(i + 1) % len(verts)]))

    # Atualiza a malha
    bm.to_mesh(mesh)
    # bm.free()

    # Muda para o modo de edição para realizar a extrusão
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    # Extruda os vértices selecionados para baixo
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, -1)}
    )

    # Alinha todos os vértices para z = 0
    bpy.ops.transform.resize(value=(1, 1, 0))

    bm = bmesh.from_edit_mesh(mesh)

    base_verts = []

    # Define a posição dos vertices criados
    for vert in bm.verts:
        if vert.select:
            vert.co.z = 0
            base_verts.append(vert.index)

    bmesh.update_edit_mesh(mesh)
    bm.free()

    bpy.ops.mesh.fill()

    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.object.mode_set(mode="OBJECT")

    return obj, base_verts


def create_road_lateral(road_object):
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")

    road_object.select_set(True)
    bpy.context.view_layer.objects.active = road_object

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")

    bpy.context.object.active_material_index = 1
    bpy.ops.object.material_slot_select()
    bpy.context.object.active_material_index = 2
    bpy.ops.object.material_slot_select()
    bpy.context.object.active_material_index = 5
    bpy.ops.object.material_slot_select()

    bpy.ops.mesh.region_to_loop()

    mesh = road_object.data
    bm = bmesh.from_edit_mesh(mesh)

    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, -1)}
    )

    bpy.ops.transform.resize(value=(1, 1, 0))

    road_lateral_base_verts = []

    for vert in bm.verts:
        if vert.select:
            vert.co.z = 0
            road_lateral_base_verts.append(vert.index)

    bmesh.update_edit_mesh(mesh)
    bm.free()

    # bpy.ops.mesh.fill()

    bpy.ops.mesh.select_more()

    bpy.ops.mesh.separate(type="SELECTED")

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")

    road_lateral_obj = bpy.data.objects.get("GeoNode_Street.001")

    road_lateral_obj.name = "RoadLateral"
    road_lateral_obj.data.name = "RoadLateral"
    road_lateral_obj.data.materials.clear()

    return road_lateral_obj, road_lateral_base_verts


def calculate_vehicle_scale(vehicle_object, lane_width, scale_factor=0.8):
    # Obtém as coordenadas dos vértices do bound_box
    bbox = [
        vehicle_object.matrix_world @ Vector(corner)
        for corner in vehicle_object.bound_box
    ]

    # Calcula a largura do veículo no eixo Y
    vehicle_width = bbox[4][1] - bbox[0][1]
    if vehicle_width == 0:
        vehicle_width = max(bbox[4][0] - bbox[0][0], bbox[4][2] - bbox[0][2])

    # Calcula a escala necessária para que o veículo caiba em uma faixa da estrada
    lane_scale = lane_width * scale_factor
    scale_factor = lane_scale / vehicle_width
    return (scale_factor, scale_factor, scale_factor)


def add_vehicle_to_scene(
    filepath,
    location=(0, 0, 0),
    rotation=(0, 0, 0),
    road_width=10,
    lane_fraction=0.8,
    vehicle_scale_factor=0.5,
    height_offset=0.1,
):
    # Importa o objeto do homem
    bpy.ops.import_scene.fbx(filepath=filepath)

    # Obtém o objeto importado
    imported_objects = bpy.context.selected_objects
    if not imported_objects:
        print("Falha ao importar o objeto. Verifique o caminho do arquivo.")
        return

    vehicle_object = imported_objects[0]

    # Calcula a largura de uma faixa
    lane_width = road_width * lane_fraction / 2

    # Calcula a escala necessária para o veículo
    # scale = calculate_vehicle_scale(vehicle_object, lane_width, vehicle_scale_factor)

    # Ajusta a localização, rotação e a escala do veículo
    vehicle_object.location = (
        location[0],
        location[1],
        location[2] + height_offset,
    )
    vehicle_object.rotation_euler = rotation
    # vehicle_object.scale = scale

    # Deseleciona todos os objetos para evitar interferência
    bpy.ops.object.select_all(action="DESELECT")

    # Seleciona o objeto do veículo e o torna ativo
    vehicle_object.select_set(True)
    bpy.context.view_layer.objects.active = vehicle_object

    # Aplica a rotação e a escala
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    print(f"Veículo adicionado à cena com a posição ajustada para {location}")

    return vehicle_object


def add_man_to_scene(
    filepath, location=(0, 0, 0), rotation=(0, 0, 0), height_offset=0.1
):
    # Importa o objeto do homem
    bpy.ops.import_scene.fbx(filepath=filepath)

    # Obtém o objeto importado
    imported_objects = bpy.context.selected_objects
    if not imported_objects:
        print("Falha ao importar o objeto. Verifique o caminho do arquivo.")
        return

    man_object = imported_objects[0]

    # Ajusta a localização, rotação e a escala do veículo
    man_object.location = (
        location[0],
        location[1],
        location[2] + height_offset,
    )
    man_object.rotation_euler = rotation

    # Deseleciona todos os objetos para evitar interferência
    bpy.ops.object.select_all(action="DESELECT")

    # Seleciona o objeto do veículo e o torna ativo
    man_object.select_set(True)
    bpy.context.view_layer.objects.active = man_object

    # Aplica a rotação e a escala
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    print(f"Homem adicionado à cena com a posição ajustada para {location}")

    return man_object


def group_objects_as_parent(parent_name, objects, location=(0, 0, 0)):
    # Cria um objeto pai vazio
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
    parent_object = bpy.context.object
    parent_object.name = parent_name

    # Define o objeto pai para todos os objetos fornecidos
    for obj in objects:
        obj.parent = parent_object

    return parent_object


def group_objects_as_existing_parent(parent_obj, objects, keep_transform=False):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    parent_obj.select_set(True)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parent_obj

    bpy.ops.object.parent_set(type="OBJECT", keep_transform=keep_transform)

    return parent_obj


def create_empty(name, location):
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
    obj = bpy.context.object
    obj.name = name

    return obj


def align_objects_along_line(parent_object, points, offset_distance=0):
    first_point = Vector(points[0])
    second_point = Vector(points[1])
    direction = (first_point - second_point).normalized()

    print(
        f"direção entre o centro do terreno e o ponto da estrada: {direction}"
    )

    # Calculate the rotation quaternion to align the object's left side (usually the X-axis) to the direction
    rotation_quat = direction.to_track_quat("X", "Z")

    # Apply the rotation to the object
    parent_object.rotation_euler = rotation_quat.to_euler()

    front = Vector((0, 0, 1))

    # Calculate the perpendicular vector
    perpendicular = front.cross(direction)

    # Offset the midpoint
    offset_pos = first_point + perpendicular * offset_distance

    # Posiciona e orienta o objeto pai ao longo da linha
    parent_object.location = offset_pos


def join_lateral_objects(lateral_obj, road_lateral_obj):
    bpy.ops.object.select_all(action="DESELECT")

    road_lateral_obj.select_set(True)
    lateral_obj.select_set(True)
    bpy.context.view_layer.objects.active = lateral_obj
    bpy.ops.object.join()
    bpy.ops.object.shade_auto_smooth()

    bpy.ops.object.select_all(action="DESELECT")


# ============================================================================================================================
# Limpa a cena antes de adicionar o veículo
clear_scene()

# Diretorio principal de arquivos
current_script_path = os.path.abspath(__file__)
current_script_directory = os.path.dirname(current_script_path)

# Obtém os argumentos da linha de comando
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1 :]  # Pega apenas os argumentos após "--"
    if len(argv) >= 2:
        csv_file_path = argv[0]  # Primeiro argumento é o CSV
        output_file = argv[1]  # Segundo argumento é o GLB
        print(f"Usando arquivo CSV: {csv_file_path}")
        print(f"Arquivo de saída GLB: {output_file}")
    else:
        print(
            "ERRO: Argumentos insuficientes. Uso: blender --background --python script.py -- input.csv output.glb"
        )
        sys.exit(1)
else:
    print("ERRO: Argumentos não encontrados após '--'")
    sys.exit(1)

# Ler os dados do CSV
points, front_points, terrain_colors, road_points = read_csv_data(csv_file_path)

# Valor para aumentar o eixo Z
terrain_z_offset = 1.5
# Aumentar todos os valores do eixo Z
points[:, 2] += terrain_z_offset
front_points = [(x, y, z + terrain_z_offset) for (x, y, z) in front_points]
road_points = [(x, y, z + terrain_z_offset) for (x, y, z) in road_points]

terrain_colors = change_yellow_points(points, terrain_colors)

# ============================================
# Cria uma nova malha e um novo objeto
mesh = bpy.data.meshes.new(name="PointCloud")
obj = bpy.data.objects.new(name="PointCloud", object_data=mesh)

# Adiciona o objeto ao contexto da cena
bpy.context.collection.objects.link(obj)

# Define a geometria da malha
mesh.from_pydata(points, [], [])
mesh.update()

# Encontrar a casca convexa
hull_points = find_convex_hull(points)

# ============================================
# Cria uma nova malha e um novo objeto
mesh = bpy.data.meshes.new(name="PointCloudConvex")
obj_conv = bpy.data.objects.new(name="PointCloudConvex", object_data=mesh)

# Adiciona o objeto ao contexto da cena
bpy.context.collection.objects.link(obj_conv)

# Define a geometria da malha
mesh.from_pydata(hull_points, [], [])
mesh.update()

# Encontrar o menor valor de Z de todos os pontos gerados
min_z = np.min(points[:, 2])

# Projetar os pontos da casca convexa no plano XY
projected_points = project_to_xy(hull_points, min_z)

# ============================================
# Cria uma nova malha e um novo objeto
mesh = bpy.data.meshes.new(name="PointCloudProjection")
obj_proj = bpy.data.objects.new(name="PointCloudProjection", object_data=mesh)

# Adiciona o objeto ao contexto da cena
bpy.context.collection.objects.link(obj_proj)

# Define a geometria da malha
mesh.from_pydata(projected_points, [], [])
mesh.update()

# Encontrar as faces
faces = find_lateral_faces(hull_points, projected_points)

# ============================================
# Combinar pontos da casca convexa e pontos projetados
combined_points = combine_points_and_projected(hull_points, projected_points)

# Obter os índices dos pontos que devem ser conectados para gerar as faces
faces_indices = get_faces_indices(combined_points, faces)

# Converter pontos para uma lista de tuples
points_list = combined_points.tolist()

# Criar a malha no Blender
lateral_obj, lateral_base_verts = create_lateral_mesh(
    hull_points, "TerrainLateral"
)

# ============================================

# ============================================
# cria o objeto do terreno (superficie)

# Realizar a triangulação de Delaunay
faces_surface_indices = delaunay_triangulation(points)

# Converter pontos para uma lista de tuples
vertices = [tuple(point) for point in points]

# Criar a superfície no Blender
terrain_obj = create_surface_faces(
    vertices, faces_surface_indices, terrain_colors
)

# ============================================

# road_line_points = road_points
front_line_points = front_points

# road_line_points = [(x, y, max(z, 0)) for x, y, z in road_line_points]

# Armazena o ponto ao centro dentre os pontos existentes
terrain_center = get_midpoint(vertices)
front_midpoint = get_midpoint(front_line_points)
# road_midpoint = get_midpoint(road_line_points)

# Ordena os pontos da rua e os pontos da frente
front_line_points = sort_points(
    points=front_line_points,
    road_center=front_midpoint,
    terrain_center=terrain_center,
)


# Sauviza os pontos da frente do terreno
normalize_vertices_to_zero([lateral_obj])
move_vertices_to_zero(lateral_obj, lateral_base_verts)

smooth_objects([terrain_obj])

first_front_point = Vector(front_line_points[0])
last_front_point = Vector(front_line_points[-1])
front_midpoint = (first_front_point + last_front_point) / 2

# Usa os pontos da frente como base para a rua
road_line_points = [first_front_point, last_front_point]
road_line_points = subdivide_points(
    points=road_line_points, num_subdivisions=13
)
road_midpoint = get_midpoint(road_line_points)

# Calcula os vetores de direção.
dir = (front_midpoint - terrain_center).normalized()
left_dir = (last_front_point - first_front_point).normalized()
farthest_vertex = farthest_vertex_in_direction(vertices=vertices, direction=dir)
road_offset = 5
# road_offset = 0

# Projeta os pontos da rua na frente do terreno.
road_line_points = project_road_on_front_points(farthest_vertex, left_dir)
road_line_points = move_points(
    np.array(vertices), np.array(road_line_points), dir, road_offset
)
# Ajuste sutil da altura mantendo o perfil
small_offset = 0.01  # Ajuste este valor conforme necessário
road_line_points = [(x, y, z - small_offset) for (x, y, z) in road_line_points]

# Ordena os pontos novamente por garantia.
road_midpoint = get_midpoint(road_line_points)
road_line_points = sort_points(
    points=road_line_points,
    road_center=road_midpoint,
    terrain_center=terrain_center,
)

# Armazena o ponto do meio relativo ao primeiro e o uiltimo pontos.
first_road_point = Vector(road_line_points[0])
last_road_point = Vector(road_line_points[len(road_line_points) - 1])
road_midpoint = (first_road_point + last_road_point) / 2
front_distance = (last_road_point - first_road_point).length

# ============================================

blend_file_path = current_script_directory + "/Assets/MaskTest.blend"
object_name = "GeoNode_Street"

road, road_line_points = get_street_with_curve(
    blend_file_path, object_name, road_line_points, lateral_obj
)

road_lateral_obj, road_lateral_base_verts = create_road_lateral(road)

# =============================================
# Configurar câmera e luz
setup_camera_and_light(points)

# =============================================
# Desabilita alguns objetos da cena
object_names = ["PointCloud", "PointCloudConvex", "PointCloudProjection"]
disable_objects_from_render(object_names)
hide_objects(object_names)

# =============================================

# Parâmetros para a cena
terrain_size = 20
num_trees = 3
num_bushes = 15
num_materials = 2

# Subdividindo o plano para mais detalhes
subdivide_object(terrain_obj, cuts=3)

# Adicionando árvores ao terreno
# created_trees = create_trees(num_trees, terrain_obj, tree_presets)

# Adicionando árvores ao terreno usando pontos específicos
# created_trees = create_trees(num_trees, terrain=terrain_obj, points=points, tree_presets=tree_presets)

# Aplicando cores às árvores e folhas
# apply_tree_colors(created_trees, trunk_colors, leaf_colors)

# Adicionando arbustos ao terreno
# create_bushes(num_bushes, terrain_obj)

# Adicionando arbustos ao terreno usando pontos específicos
# create_bushes(num_bushes, terrain=terrain_obj, points=points)

# Adicionando grama ao terreno
# create_grass(terrain_obj)

# ====================================================================

# Path to the Blender file containing the material
material_file_path = current_script_directory + "/Assets/MaskTest.blend"
material_name = "TerrainMask_BW"

# Pega o material com mascara
mask_material = get_external_material(material_file_path, material_name)

material_name = "TerrainLateralMatDino"
soil_material = get_external_material(material_file_path, material_name)

# Aplica o material ao objeto criado
apply_material_to_object(lateral_obj, soil_material)

# Aplica o material ao objeto criado
apply_material_to_object(road_lateral_obj, soil_material)

apply_material_to_object(terrain_obj, mask_material)

create_uv_map([terrain_obj, lateral_obj, road_lateral_obj])

# =============================================
# Atualizando a visualização
try:
    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
except RuntimeError:
    print("Skipping redraw in background mode")

# =============================================
# realizando a exportaçao do modelo

# Certifique-se de que você está no modo de objeto
if bpy.ops.object.mode_set.poll():
    bpy.ops.object.mode_set(mode="OBJECT")

# Deseleciona todos os objetos para garantir um estado limpo
bpy.ops.object.select_all(action="DESELECT")

# # Seleciona todos os objetos da cena
# for obj in bpy.data.objects:
#     obj.select_set(True)

# Get the active view layer
view_layer = bpy.context.view_layer

# Iterate over objects in the view layer and select them
for layer_collection in view_layer.layer_collection.children:
    for obj in layer_collection.collection.objects:
        obj.select_set(True)

# Define o objeto ativo (necessário para algumas operações)
bpy.context.view_layer.objects.active = bpy.data.objects[0]

# Exemplo de uso das funções
car_filepath = (
    current_script_directory + "/Assets/honda_city/HondaCityCar.fbx"
)  # Substitua pelo caminho real do arquivo
man_filepath = (
    current_script_directory + "/Assets/man/MaleOBJStandingPose.fbx"
)  # Substitua pelo caminho real do arquivo
sidewalk_width = 2
road_width = 6  # Largura da estrada
car_location = (-5, 3, 0)  # Posição do veículo na estrada
car_rotation = (
    1.5708,
    0,
    1.5708,
)  # Rotaciona o veículo 90 graus em torno do eixo Z

man_location = (-3, 1, 0)  # Posição do homem na estrada
man_rotation = (
    1.5,
    0,
    0,
)  # Rotaciona o homen para que ele fique paralelo ao carro

car_height_offset = 0.75  # Offset para elevar o veículo acima da estrada
man_height_offset = 0.225  # Offset para elevar o personagem acima da estrada

# Adiciona o veículo à estrada
vehicle_object = add_vehicle_to_scene(
    car_filepath,
    car_location,
    car_rotation,
    road_width,
    height_offset=car_height_offset,
)
man_object = add_man_to_scene(
    man_filepath, man_location, man_rotation, man_height_offset
)

# Agrupa a estrada, a faixa e o veículo em um objeto pai
parent_object = group_objects_as_parent(
    "CarAndManWithRoad", [vehicle_object, man_object]
)

# print("Road points")
# print(road_points)
# print("Road line points")
# print(road_line_points)

# Alinha o objeto pai ao longo da reta
align_objects_along_line(
    parent_object, road_line_points, (road_width + sidewalk_width * 2) * -0.5
)

group_objects_as_existing_parent(parent_object, [road, road_lateral_obj], True)

center_object = create_empty("CenterParent", parent_object.location)

align_objects_along_line(
    center_object,
    [road_midpoint, last_road_point],
    (road_width + sidewalk_width * 2) * -0.5,
)
group_objects_as_existing_parent(center_object, [parent_object], True)

move_vertices_to_zero(road_lateral_obj, road_lateral_base_verts)

join_lateral_objects(lateral_obj=lateral_obj, road_lateral_obj=road_lateral_obj)

# Gera as imagens dos materias antes de exportar
bake_diffuse_color([terrain_obj, lateral_obj])

# Exporta a cena para glTF
bpy.ops.export_scene.gltf(filepath=output_file, export_format="GLB")

# # Coordenadas da frente do lote
# print("Front points")
# print(front_points)
# print("Front line points")
# print(front_line_points)

# Get command line arguments after "--"
argv = sys.argv
argv = argv[argv.index("--") + 1 :]  # Get all args after "--"

if len(argv) != 2:
    print(
        "Usage: blender --background --python script.py -- <input_csv_path> <output_glb_path>"
    )
    sys.exit(1)

# Parse arguments
input_csv_path = argv[0]
output_glb_path = argv[1]

# Get the directory of the current script
current_script_directory = os.path.dirname(os.path.abspath(__file__))

# Get the directory of the input CSV file
input_directory = os.path.dirname(input_csv_path)


def clear_scene():
    """Clear all objects from the scene"""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def main():
    # Clear the scene
    clear_scene()
    print("Scene cleared")

    # Read CSV data
    points, front_points, terrain_colors, road_points = read_csv_data(
        input_csv_path
    )
    print(
        f"Data read from CSV: {len(points)} points, {len(front_points)} front points, {len(road_points)} road points"
    )

    # Terrain Z offset
    terrain_z_offset = 1.5
    points[:, 2] += terrain_z_offset
    front_points = [(x, y, z + terrain_z_offset) for (x, y, z) in front_points]
    road_points = [(x, y, z + terrain_z_offset) for (x, y, z) in road_points]

    # Update asset paths to use current_script_directory
    blend_file_path = os.path.join(
        current_script_directory, "Assets", "MaskTest.blend"
    )
    car_filepath = os.path.join(
        current_script_directory, "Assets", "honda_city", "HondaCityCar.fbx"
    )
    man_filepath = os.path.join(
        current_script_directory, "Assets", "man", "MaleOBJStandingPose.fbx"
    )

    # ... (rest of your main function code) ...

    # Before export, let's verify what objects are in the scene
    print("\nObjects in scene before export:")
    for obj in bpy.data.objects:
        print(f"- {obj.name} ({obj.type})")
        if obj.hide_render:
            print("  WARNING: This object is hidden from render")
        if not obj.visible_get():
            print("  WARNING: This object is not visible")

    # Deselect all objects first
    bpy.ops.object.select_all(action="DESELECT")

    # List of objects we want to export
    objects_to_export = [
        "Terrain",
        "TerrainLateral",
        "GeoNode_Street",
        "HondaCityCarLowPo.001",
        "MalePoseOBJ",
    ]

    # Get the active view layer
    view_layer = bpy.context.view_layer

    # Select and make visible all objects we want to export
    for obj_name in objects_to_export:
        if obj_name in bpy.data.objects:
            obj = bpy.data.objects[obj_name]
            obj.hide_viewport = False
            obj.hide_render = False
            obj.hide_set(False)
            obj.select_set(True)

            # Make this the active object
            view_layer.objects.active = obj

    # Ensure we're in object mode if we have an active object
    if view_layer.objects.active:
        if view_layer.objects.active.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    # Export the scene
    try:
        bpy.ops.export_scene.gltf(
            filepath=output_glb_path,
            export_format="GLB",
            use_selection=False,  # Changed to False to export all visible objects
        )
        print(f"Scene exported to: {output_glb_path}")

        # Verify the export
        if os.path.exists(output_glb_path):
            file_size = os.path.getsize(output_glb_path)
            print(f"Exported file size: {file_size/1024:.2f}KB")
        else:
            print("WARNING: Export file was not created!")
    except Exception as e:
        print(f"Error during export: {str(e)}")


def export_scene_to_glb(output_file):
    """
    Exporta a cena para formato GLB com configurações otimizadas
    """
    try:
        # Garante que estamos no modo objeto
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
            print("Modo alterado para 'OBJECT'.")
        else:
            print("Não foi possível alterar o modo para 'OBJECT'.")

        # Força uma atualização da cena
        bpy.context.view_layer.update()
        print("Cena atualizada.")

        # Lista de objetos que devem ser exportados
        export_objects = [
            "Terrain",
            "TerrainLateral",
            "GeoNode_Street",
            "HondaCityCarLowPo",
            "MalePoseOBJ",
        ]

        # Verifica a existência dos objetos na cena
        existing_objects = []
        for obj_name in export_objects:
            obj = bpy.data.objects.get(obj_name)
            if obj:
                existing_objects.append(obj)
                print(f"Objeto encontrado: {obj_name}")
            else:
                print(f"Aviso: Objeto '{obj_name}' não encontrado na cena.")

        if not existing_objects:
            print(
                "ERRO: Nenhum dos objetos de exportação foi encontrado. Abortando exportação."
            )
            return False

        # Deseleciona todos os objetos
        bpy.ops.object.select_all(action="DESELECT")
        print("Todos os objetos foram desmarcados.")

        # Seleciona apenas os objetos necessários
        for obj in existing_objects:
            obj.select_set(True)
            print(f"Objeto selecionado para exportação: {obj.name}")

        # Define o objeto ativo (necessário para alguns operadores)
        bpy.context.view_layer.objects.active = existing_objects[0]
        print(f"Objeto ativo definido para: {existing_objects[0].name}")

        # Verifica quantos objetos estão selecionados
        selected_objects = [obj for obj in bpy.context.selected_objects]
        print(
            f"Número de objetos selecionados para exportação: {len(selected_objects)}"
        )
        for obj in selected_objects:
            print(f"- {obj.name}")

        # Configurações de exportação
        export_settings = {
            "filepath": output_file,
            "export_format": "GLB",
            "use_selection": True,
            "export_draco_mesh_compression_enable": True,
            "export_draco_mesh_compression_level": 6,
            # Adicione outras configurações conforme necessário
        }

        print("Iniciando a exportação para GLB...")
        bpy.ops.export_scene.gltf(**export_settings)
        print("Exportação concluída.")

        # Verifica o tamanho do arquivo exportado
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"Tamanho do arquivo exportado: {file_size} bytes.")
            if file_size > 1024:  # Maior que 1KB
                print(f"Cena exportada com sucesso para: {output_file}")
                print(f"Tamanho do arquivo: {file_size/1024/1024:.2f} MB")
                return True
            else:
                print(
                    f"ERRO: Arquivo GLB gerado está muito pequeno ({file_size} bytes)"
                )
                return False
        else:
            print("ERRO: Arquivo GLB não foi criado.")
            return False

    except Exception as e:
        print(f"Erro ao exportar: {str(e)}")
        return False


# ... resto do código ...


# Antes da exportação, adicione uma função para listar todos os objetos na cena
def list_scene_objects():
    print("Objetos atuais na cena:")
    for obj in bpy.data.objects:
        visibility = []
        if not obj.visible_get():
            visibility.append("não visível")
        if not obj.visible_get(view_layer=bpy.context.view_layer):
            visibility.append("escondido na renderização")
        visibility_status = ", ".join(visibility) if visibility else "visível"
        print(f"- {obj.name} ({obj.type}) - {visibility_status}")


# Chamada da função de listagem para debug
list_scene_objects()


# Procedimento principal do script
def main():
    # ... código de criação de terreno e outros objetos ...

    # Após criar e configurar todos os objetos, liste-os para debug
    print("Objetos na cena após criação:")
    list_scene_objects()

    # Defina o arquivo de saída baseado nos argumentos do script
    import sys

    if "--" in sys.argv:
        idx = sys.argv.index("--")
        if len(sys.argv) > idx + 2:
            input_csv = sys.argv[idx + 1]
            output_file = sys.argv[idx + 2]
        else:
            print("ERRO: Argumentos insuficientes fornecidos.")
            return
    else:
        print("ERRO: Argumentos não encontrados.")
        return

    # Chama a função de exportação
    if export_scene_to_glb(output_file):
        print("Exportação concluída com sucesso!")
    else:
        print("Houve um erro na exportação.")

    # Opcional: Limpa a cena após exportação
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("Cena limpa após exportação.")


# Chamada da função principal
if __name__ == "__main__":
    main()


def create_road_mesh(front_line_points, terrain_center):
    """
    Cria a malha da rua baseada nos pontos da frente do terreno.
    """
    print("\n=== Criando malha da rua ===")
    print(f"Pontos da frente do terreno: {front_line_points}")

    # Pega os pontos extremos da frente
    first_front_point = Vector(front_line_points[0])
    last_front_point = Vector(front_line_points[-1])
    print(f"Primeiro ponto da frente: {first_front_point}")
    print(f"Último ponto da frente: {last_front_point}")

    # Calcula a direção da rua baseada nos pontos da frente
    road_direction = (last_front_point - first_front_point).normalized()
    print(f"Direção da rua: {road_direction}")

    # Largura da rua
    road_width = 5.0

    # Cria os pontos da rua mantendo a inclinação
    num_segments = 10
    road_points = []

    for i in range(num_segments + 1):
        # Interpola a posição entre o primeiro e último ponto
        t = i / num_segments
        # Interpola todos os componentes (x, y, z) para manter a inclinação
        current_pos = Vector(
            (
                first_front_point.x * (1 - t) + last_front_point.x * t,
                first_front_point.y * (1 - t) + last_front_point.y * t,
                first_front_point.z * (1 - t)
                + last_front_point.z * t,  # Interpola a altura
            )
        )

        # Cria o vetor perpendicular para a largura da rua
        # Usando o produto vetorial com o vetor UP (0,0,1) para garantir que seja horizontal
        width_direction = road_direction.cross(Vector((0, 0, 1))).normalized()

        # Cria os dois pontos da rua (esquerda e direita)
        left_point = current_pos + width_direction * road_width
        right_point = current_pos - width_direction * road_width

        road_points.append(left_point.to_tuple())
        road_points.append(right_point.to_tuple())
        print(f"Ponto da rua {i}: {road_points[-2]}, {road_points[-1]}")

    # Cria as faces da rua
    faces = []
    for i in range(num_segments):
        v1 = i * 2
        v2 = v1 + 1
        v3 = v1 + 2
        v4 = v1 + 3
        faces.append((v1, v2, v4, v3))
        print(f"Face da rua {i}: {(v1, v2, v4, v3)}")

    # Cria a malha
    road_mesh = bpy.data.meshes.new("Road")
    road_mesh.from_pydata(road_points, [], faces)
    road_mesh.update()

    # Cria o objeto
    road_obj = bpy.data.objects.new("GeoNode_Street", road_mesh)
    bpy.context.scene.collection.objects.link(road_obj)

    print("=== Malha da rua criada ===\n")
    return road_obj


# ... (resto do código permanece igual) ...

# Quando for criar a rua
road_obj = create_road_mesh(front_line_points, terrain_center)
