"""Fantasy Island Simulator for Maya 2026.

Paste this complete file into Maya's Python Script Editor and run it.
The tool creates a low-poly, seasonal island for a cozy world-building game.
Every object made by the tool stays inside one root group, so it can be
rebuilt, undone, or deleted without touching another artist's scene.
"""

import json
import math
import random
from contextlib import contextmanager

# This serves to make Python understand Maya language.
import maya.cmds as cmds
import maya.api.OpenMaya as om

WINDOW = "fantasyIslandWindow"
ROOT = "fantasyIsland_GRP"
GROUPS = {
    "environment": "island_environment_GRP", "castle": "island_castle_GRP",
    "trees": "island_trees_GRP", "houses": "island_houses_GRP",
    "clouds": "island_clouds_GRP", "sheep": "island_sheep_GRP",
    "monsters": "island_monsters_GRP", "villagers": "island_villagers_GRP",
    "lights": "island_lights_GRP", "sky": "island_sky_GRP",
    "weather": "island_weather_GRP",
}

# Placement points follow the crescent's solid ground, never its central bay.
TREE_POINTS = [
    (-10, -3), (-9, 1), (-8, 5), (-7, -6), (-7, 3), (-6, 7),
    (-6, -1), (-5, -7), (11.4, -5.2), (-4, 5), (-3, -5), (-2, 7),
    (-1, -7), (0, 6), (1, -7), (2, 6), (3, -5), (4, 4),
    (5, -3), (5, 5), (6, 3), (7, -2), (-10, 4), (-7, -1),
    (-4, 3), (-2, -4), (1, 4), (3, -4), (4, 5), (6, 2),
]
HOUSE_POINTS = [
    (-1, 4), (1, 4), (2.5, 4.2), (11.5, -5.1), (5.2, 3.1),
    (.6, 5.8), (3.2, 5.6), (5.1, 4.8), (-1.2, 5.3), (-2.4, 3.7),
]
SHEEP_POINTS = [
    (-6, -5), (-4, -6), (-1, -6), (2, -5), (4, -4),
    (5, -3), (-8, -2), (-8, 2), (-6, 6), (-2, 6),
    (2, 5), (4, 4), (6, 3), (-9, 0), (-5, 1),
]
MONSTER_POINTS = [
    (-10, -3), (5, -3), (-9, 5), (5, 3),
    (-9, 0), (-4, 7), (-4, -7), (1, -7),
]
VILLAGER_POINTS = [
    (-.5, 4.1), (1.0, 4.0), (2.6, 4.0), (3.8, 3.5), (5.1, 3.0),
    (3.6, 4.9), (4.8, 4.1), (1.9, 5.1), (.2, 4.8), (-1.4, 3.8),
]
CASTLE_SITE = (-7.2, 4.2)
VILLAGE_SITE = (1.6, 4.8)

# Faceted landforms make an open C/crescent, with a separate outpost island
# across the eastern bay instead of the old single oval island.
LAND_FORMS = (
    (-6.0, 1.0, -6.3, 5.9, 1.6, 3.2),
    (-9.3, 2.0, -3.2, 4.2, 2.6, 3.9),
    (-9.1, 2.6,  .9, 4.4, 3.1, 4.2),
    (-7.1, 3.7,  4.3, 5.2, 3.7, 3.7),
    (-2.6, 2.8,  6.4, 5.4, 3.1, 3.2),
    ( 2.2, 2.25, 5.2, 4.9, 2.6, 3.0),
    ( 5.5, 1.3,  3.2, 3.2, 1.5, 1.8),
    (-1.0, 2.1, -7.0, 5.3, 2.3, 2.8),
    ( 3.1, 2.3, -5.4, 5.0, 2.7, 3.1),
    ( 6.1, 1.2, -2.8, 3.2, 1.4, 1.8),
    (-5.0, 2.2,  1.1, 4.0, 2.8, 4.0),
    (11.7, .52, -5.3, 2.35, .95, 1.85),
    (13.0, .38, -5.0, 1.35, .72, 1.12),
    (10.8, .28,  5.9, 1.35, .58, 1.05),
    (-13.4, .26, 5.4, 1.30, .56, 1.00),
    (-12.3, .27, -7.2, 1.50, .60, 1.05),
    ( 8.8, .25,  8.0, 1.40, .52, 1.02),
    (13.2, .30,  1.2, 1.50, .65, 1.10),
)
ISLET_SITES = ((10.8, 5.9), (-13.4, 5.4), (-12.3, -7.2),
               (8.8, 8.0), (13.2, 1.2))
RIVER_ROUTE = (
    (-4.7, 7.0), (-6.3, 4.6), (-6.2, 1.2), (-4.3, -2.2),
    (-1.3, -5.2), (2.5, -5.6), (5.8, -3.2),
)

SEASONS = {
    "Spring": {
        "leaf": (.24, .48, .22), "sky": (.42, .64, .78),
        "deep_rock": (.07, .15, .16), "blue_rock": (.14, .29, .28),
        "violet_rock": (.23, .31, .27), "lavender_rock": (.34, .43, .36),
        "water": (.06, .34, .47), "detail": (.96, .47, .62),
        "snow": (.85, .90, .88), "snow_light": (.94, .98, .95),
    },
    "Summer": {
        "leaf": (.13, .34, .18), "sky": (.25, .53, .76),
        "deep_rock": (.05, .11, .12), "blue_rock": (.10, .23, .20),
        "violet_rock": (.17, .25, .17), "lavender_rock": (.28, .36, .23),
        "water": (.02, .24, .48), "detail": (.97, .78, .26),
        "snow": (.82, .88, .82), "snow_light": (.91, .96, .89),
    },
    "Autumn": {
        "leaf": (.52, .20, .09), "sky": (.53, .37, .49),
        "deep_rock": (.13, .075, .065), "blue_rock": (.25, .14, .10),
        "violet_rock": (.33, .18, .10), "lavender_rock": (.40, .25, .15),
        "water": (.12, .18, .34), "detail": (.84, .28, .10),
        "snow": (.73, .58, .49), "snow_light": (.82, .66, .54),
    },
    "Winter": {
        "leaf": (.33, .42, .40), "sky": (.31, .36, .58),
        "deep_rock": (.045, .07, .12), "blue_rock": (.09, .14, .25),
        "violet_rock": (.17, .21, .31), "lavender_rock": (.29, .35, .42),
        "water": (.14, .35, .48), "detail": (.78, .86, .96),
        "snow": (.88, .93, .97), "snow_light": (.96, .98, 1.0),
    },
}

UI = {
    "window": (.16, .11, .21),
    "header": (.47, .29, .56),
    "subheader": (.30, .20, .39),
    "life": (.30, .51, .40),
    "land": (.31, .45, .62),
    "atmosphere": (.66, .36, .42),
    "action": (.34, .31, .57),
    "build": (.31, .61, .46),
    "delete": (.59, .25, .35),
    "save": (.35, .45, .67),
}
POPULATION_CONTROLS = {
    "trees": ("treeSlider", 30),
    "houses": ("houseSlider", 10),
    "clouds": ("cloudSlider", 30),
    "sheep": ("sheepSlider", 15),
    "villagers": ("villagerSlider", 10),
    "monsters": ("monsterSlider", 8),
}
PRESET_FORMAT = "fantasy_island_blueprint"
PRESET_VERSION = 1
UNDO_DEPTH = 0
TERRAIN_SURFACES = []
CURRENT_SEASON = "Spring"
CURRENT_WEATHER = "Clear"
CURRENT_WATER_FEATURE = "Lake"


def ensure_group(name, parent=None):
    if not cmds.objExists(name):
        cmds.group(empty=True, name=name)
    if parent:
        old_parent = cmds.listRelatives(name, parent=True, fullPath=False) or []
        if old_parent != [parent]:
            cmds.parent(name, parent)
    return name


def clear_group(name):
    children = cmds.listRelatives(name, children=True, fullPath=True) or []
    if children:
        cmds.delete(children)


@contextmanager
def undo_chunk(label):
    """Wrap nested scene edits in one reliable Ctrl+Z step."""
    global UNDO_DEPTH
    is_outer_chunk = UNDO_DEPTH == 0
    if is_outer_chunk:
        cmds.undoInfo(openChunk=True, chunkName=label)
    UNDO_DEPTH += 1
    try:
        yield
    finally:
        UNDO_DEPTH -= 1
        if is_outer_chunk:
            cmds.undoInfo(closeChunk=True)


# This creates a material and gives it a color.
def material(name, colour):
    shader = name + "_MAT"
    shading_group = shader + "SG"
    if not cmds.objExists(shader):
        shader = cmds.shadingNode("lambert", asShader=True, name=shader)
        cmds.sets(renderable=True, noSurfaceShader=True, empty=True,
                  name=shading_group)
        cmds.connectAttr(shader + ".outColor", shading_group + ".surfaceShader",
                         force=True)
    cmds.setAttr(shader + ".color", colour[0], colour[1], colour[2],
                 type="double3")
    return shader


def water_material(name, colour):
    """Keep water visibly blue even under a low night-time Maya light."""
    shader = material(name, colour)
    cmds.setAttr(
        shader + ".incandescence",
        colour[0] * .11, colour[1] * .11, colour[2] * .14,
        type="double3"
    )
    return shader


def glow_material(name, colour, strength=.30):
    """A soft self-lit colour for sun, moon, and water shimmer meshes."""
    shader = material(name, colour)
    cmds.setAttr(
        shader + ".incandescence",
        colour[0] * strength, colour[1] * strength, colour[2] * strength,
        type="double3"
    )
    return shader


def bright_water(colour):
    """A readable stylised blue, rather than the almost-black night tint."""
    return (
        max(.045, colour[0] * .90),
        max(.32, colour[1] * 1.30),
        max(.58, colour[2] * 1.30),
    )


def make(command, name, pos, scale, shader, parent, rotate=(0, 0, 0), **kwargs):
    """Cree une primitive, la colore, puis la range dans son groupe."""
    node = command(name=name, **kwargs)[0]
    cmds.xform(node, worldSpace=True, translation=pos, rotation=rotate)
    cmds.setAttr(node + ".scale", scale[0], scale[1], scale[2], type="double3")
    cmds.makeIdentity(node, apply=True, translate=False, rotate=False, scale=True)
    cmds.sets(node, edit=True, forceElement=shader + "SG")
    cmds.parent(node, parent)
    return node


def make_mesh(name, vertices, faces, shader, parent):
    """Create one continuous low-poly mesh from explicit world-space points.

    This is used for water because individual cubes and cylinders can only sit
    *near* the terrain.  A mesh whose vertices sample the actual terrain never
    has stair-step seams or a single floating rim.
    """
    points = [om.MPoint(x, y, z) for x, y, z in vertices]
    counts = [len(face) for face in faces]
    connects = [vertex for face in faces for vertex in face]
    transform_object = om.MFnMesh().create(points, counts, connects)
    node = om.MFnDependencyNode(transform_object).name()
    node = cmds.rename(node, name)
    cmds.sets(node, edit=True, forceElement=shader + "SG")
    cmds.parent(node, parent)
    return node


def season():
    return CURRENT_SEASON


def set_season(value, rebuild=True):
    """Season buttons set this state; loading a blueprint can defer rebuilding."""
    global CURRENT_SEASON
    CURRENT_SEASON = value

    if cmds.control("seasonReadout", exists=True):
        cmds.text("seasonReadout", edit=True, label="CURRENT SEASON  ·  %s" % value.upper())

    if rebuild:
        apply_season(value)


def weather():
    return CURRENT_WEATHER


def set_weather(value, rebuild=True):
    """Weather is a deliberate state, not a side effect of the season."""
    global CURRENT_WEATHER
    CURRENT_WEATHER = value
    if cmds.control("weatherReadout", exists=True):
        cmds.text(
            "weatherReadout", edit=True,
            label="CURRENT WEATHER  ·  %s" % value.upper()
        )
    if rebuild and cmds.objExists(ROOT):
        with undo_chunk("Change island weather"):
            create_weather()


def ellipsoid_top(x, z, cx, cy, cz, rx, ry, rz):
    value = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
    if value >= 1.0:
        return -1000.0
    return cy + ry * math.sqrt(1.0 - value)

# One terrain formula is the source of truth for every placed object.
# All placement functions use world coordinates; terrain_y converts them back
# to the original map before calculating the surface height.
def world_seed():
    if cmds.control("worldSeedSlider", exists=True):
        return cmds.intSliderGrp("worldSeedSlider", query=True, value=True)
    return 184


def organic_point(point, index, radius):
    """Controlled variation: repeatable for a seed, never a perfect grid."""
    rng = random.Random(world_seed() * 1009 + index * 101)
    return (
        point[0] + rng.uniform(-radius, radius),
        point[1] + rng.uniform(-radius, radius),
    )


def world_xz(base_x, base_z):
    return base_x * island_width(), base_z * island_depth()


def ellipsoid_top(x, z, cx, cy, cz, rx, ry, rz):
    value = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
    if value >= 1.0:
        return -1000.0
    return cy + ry * math.sqrt(1.0 - value)


def terrain_peak_y(x, z):
    """Return the raw height of the crescent landforms, or -1000 over sea."""
    base_x = x / island_width()
    base_z = z / island_depth()
    return max(
        ellipsoid_top(base_x, base_z, cx, cy, cz, rx, ry, rz)
        for cx, cy, cz, rx, ry, rz in LAND_FORMS
    )


def terrain_y(x, z):
    """Return a safe estimated terrain height for placement before a build."""
    return max(.25, terrain_peak_y(x, z)) + .02


def is_on_island(x, z):
    """Reject open-sea positions when scattering detail and natural props."""
    return terrain_peak_y(x, z) > .55


def ground_contact_y(x, z):
    """Ray-cast onto real low-poly terrain, not the smoother height estimate."""
    if not TERRAIN_SURFACES:
        return terrain_y(x, z) - .12

    highest_hit = None
    ray_origin = om.MFloatPoint(x, 1000.0, z)
    ray_direction = om.MFloatVector(0.0, -1.0, 0.0)

    for transform in TERRAIN_SURFACES:
        shapes = cmds.listRelatives(
            transform, shapes=True, noIntermediate=True, fullPath=True
        ) or []
        for shape in shapes:
            selection = om.MSelectionList()
            selection.add(shape)
            mesh = om.MFnMesh(selection.getDagPath(0))
            hit = mesh.closestIntersection(
                ray_origin, ray_direction, om.MSpace.kWorld, 2000.0, False
            )
            if hit is not None:
                height = hit[0].y
                if highest_hit is None or height > highest_hit:
                    highest_hit = height

    if highest_hit is None:
        return terrain_y(x, z) - .12
    return highest_hit - .015


def make_materials():
    """Build a season-aware low-poly palette."""
    palette = SEASONS[season()]
    return {
        "ocean": water_material("island_ocean", bright_water(palette["water"])),
        "water": water_material("island_water", bright_water(palette["water"])),
        "deep_rock": material("island_deep_rock", palette["deep_rock"]),
        "blue_rock": material("island_blue_rock", palette["blue_rock"]),
        "violet_rock": material("island_violet_rock", palette["violet_rock"]),
        "lavender_rock": material(
            "island_lavender_rock", palette["lavender_rock"]
        ),
        "snow_shadow": material("island_snow_shadow", (.60, .66, .78)),
        "snow": material("island_snow", palette["snow"]),
        "snow_light": material("island_snow_light", palette["snow_light"]),
        "castle_stone": material("castle_stone", (.36, .40, .44)),
        "castle_dark": material("castle_dark_wood", (.13, .07, .11)),
        "castle_wood": material("castle_warm_wood", (.43, .22, .17)),
        "trunk": material("tree_trunk", (.19, .06, .08)),
        "cloud": material("cloud_cream", (.98, .86, .83)),
        "path": material("island_path_stone", (.35, .26, .22)),
        "detail": material("island_season_detail", palette["detail"]),
        "reed": material("island_reed", (.24, .31, .13)),
        "star": material("island_star", (1.0, .92, .70)),
    }


def mountain(parent, index, data):
    """Build wide, deliberately faceted cliffs instead of smooth round hills."""
    base_x, y, base_z, sx, sy, sz, shader, rotation = data
    x, z = world_xz(base_x, base_z)
    node = make(
        cmds.polySphere, "island_mountain_%02d" % index, (x, y, z),
        (sx * island_width(), sy, sz * island_depth()), shader, parent,
        (0, 0, 0), subdivisionsX=10, subdivisionsY=6
    )
    TERRAIN_SURFACES.append(node)


def snow_cap(parent, index, base_x, base_z, y, sx, sy, sz, shader, rotation):
    x, z = world_xz(base_x, base_z)
    make(
        cmds.polySphere, "island_snow_cap_%02d" % index, (x, y, z),
        (sx * island_width(), sy, sz * island_depth()), shader, parent,
        (0, rotation[1], 0), subdivisionsX=7, subdivisionsY=4
    )


def create_shore_rocks(parent, mats):
    """Broken rocky edges follow the crescent rather than outlining an oval."""
    rng = random.Random(world_seed() + 103)
    coast = (
        (-6.5, -8.8), (-10.4, -5.6), (-12.2, -1.8), (-11.7, 2.7),
        (-9.4, 6.3), (-5.4, 8.7), (-.8, 9.0), (3.6, 7.0),
        (6.9, 4.1), (7.4, 2.1), (7.2, -3.0), (4.8, -5.8),
        (.8, -8.5), (10.0, -6.7), (12.1, -7.2), (14.4, -5.5),
        (13.8, -3.8), (10.6, -3.4),
        # A few loose rocks around every satellite stop the ocean from
        # reading as an untouched perfect disk.
        (10.8, 5.9), (-13.4, 5.4), (-12.3, -7.2), (8.8, 8.0),
        (13.2, 1.2),
    )

    rock_index = 0
    for anchor_x, anchor_z in coast:
        for _ in range(3):
            base_x = anchor_x + rng.uniform(-.80, .80)
            base_z = anchor_z + rng.uniform(-.62, .62)
            x, z = world_xz(base_x, base_z)
            tide_profile = rng.uniform(-.72, -.06)
            size = rng.uniform(.40, 1.45)
            make(
                cmds.polySphere, "island_shore_rock_%02d" % rock_index,
                (x, tide_profile, z),
                (size * island_width(), size * rng.uniform(.14, .52),
                 size * island_depth() * rng.uniform(.55, 1.35)),
                mats["deep_rock"] if rock_index % 3 else mats["blue_rock"], parent,
                (rng.uniform(0, 55), rng.uniform(0, 360), rng.uniform(0, 55)),
                subdivisionsX=7, subdivisionsY=4
            )
            rock_index += 1


def create_beaches(parent, mats):
    """Make angular, uneven shore ramps instead of one uniform cliff band.

    The first row samples real island ground.  The next two rows descend at
    different rates and finish *under* the sea.  This intentionally gives the
    coastline a mixture of dry beach, shallow shelf, and broken rock.
    """
    sand = material("island_beach_sand", (.57, .48, .31))
    shore_sites = (
        # base X/Z, outward normal, half-width, submerged depth, material
        (-1.3, 8.1, 0.0, 1.0, 2.55, .56, sand),
        (6.4, -3.3, 1.0, -.20, 1.65, .74, mats["blue_rock"]),
        (-6.5, -7.8, -.18, -1.0, 2.10, .48, sand),
        (-11.8, 2.6, -1.0, .15, 1.85, .82, mats["deep_rock"]),
        (7.1, 2.2, 1.0, .15, 1.50, .64, mats["violet_rock"]),
    )
    rng = random.Random(world_seed() + 407)

    for index, (base_x, base_z, normal_x, normal_z, half_width, depth, shader) in enumerate(shore_sites):
        normal_length = math.sqrt(normal_x ** 2 + normal_z ** 2)
        normal_x, normal_z = normal_x / normal_length, normal_z / normal_length
        tangent_x, tangent_z = -normal_z, normal_x
        row_offsets = (-.68, .24, 1.18 + rng.uniform(-.12, .22))
        vertices = []
        divisions = 5

        for row, offset in enumerate(row_offsets):
            for column in range(divisions):
                fraction = column / float(divisions - 1) - .5
                along = fraction * half_width * 2.0
                # A different edge for every segment prevents a neat rectangle.
                wobble = rng.uniform(-.15, .15) if row else rng.uniform(-.07, .07)
                local_x = base_x + tangent_x * along + normal_x * (offset + wobble)
                local_z = base_z + tangent_z * along + normal_z * (offset + wobble)
                x, z = world_xz(local_x, local_z)
                ground_y = ground_contact_y(x, z)
                if row == 0:
                    y = ground_y + .015
                elif row == 1:
                    # Each midpoint has a different height: a beach is not a
                    # perfectly straight extrusion from the mountain.
                    y = max(-.18, ground_y * rng.uniform(.28, .58))
                else:
                    # Let the outer lip disappear below the ocean top (-.30).
                    y = -.30 - depth * rng.uniform(.72, 1.12)
                vertices.append((x, y, z))

        faces = []
        for row in range(len(row_offsets) - 1):
            for column in range(divisions - 1):
                current = row * divisions + column
                below = current + divisions
                # This winding points up, so an illuminated sandy shelf does
                # not accidentally render as the dark underside of a mesh.
                faces.append((current, current + 1, below + 1, below))

        node = make_mesh("island_eroded_shore_%02d" % index, vertices, faces,
                         shader, parent)
        TERRAIN_SURFACES.append(node)


def create_side_islet_details(parent, mats):
    """Give the small side islands their own grounded, varied landmarks."""
    rng = random.Random(world_seed() + 619)
    trunk = material("islet_tree_trunk", (.20, .075, .045))
    leaves = material("islet_tree_leaves", SEASONS[season()]["leaf"])
    light_leaves = material(
        "islet_tree_light_leaves",
        tuple(min(1.0, channel * 1.32 + .05)
              for channel in SEASONS[season()]["leaf"])
    )
    snow = material("islet_tree_snow", SEASONS["Winter"]["snow_light"])

    for index, (base_x, base_z) in enumerate(ISLET_SITES):
        islet_group = cmds.group(
            empty=True, name="island_side_islet_%02d_GRP" % index,
            parent=parent
        )

        # Low stones make every islet feel like it rose from the water rather
        # than like a copy-pasted green pebble.
        for rock in range(2):
            angle = rng.uniform(0.0, math.tau)
            distance = rng.uniform(.38, .76)
            rock_x, rock_z = world_xz(
                base_x + math.cos(angle) * distance,
                base_z + math.sin(angle) * distance
            )
            rock_height = rng.uniform(.12, .24)
            y = ground_contact_y(rock_x, rock_z)
            make(
                cmds.polySphere, "islet_%02d_rock_%02d" % (index, rock),
                (rock_x, y + rock_height, rock_z),
                (rng.uniform(.22, .46), rock_height, rng.uniform(.24, .52)),
                mats["blue_rock"] if (index + rock) % 2 else mats["deep_rock"],
                islet_group,
                (rng.uniform(0, 35), rng.uniform(0, 360), rng.uniform(0, 35)),
                subdivisionsX=6, subdivisionsY=4
            )

        # Four deliberately small trees (and one bare rocky islet) create a
        # distant, habitable archipelago without crowding the little beaches.
        if index != 2:
            tree_x, tree_z = world_xz(
                base_x + rng.uniform(-.18, .18),
                base_z + rng.uniform(-.16, .16)
            )
            y = ground_contact_y(tree_x, tree_z)
            height = rng.uniform(.78, 1.08)
            make(
                cmds.polyCylinder, "islet_tree_%02d_trunk" % index,
                (tree_x, y + height * .50, tree_z),
                (.075, height * .50, .075), trunk, islet_group,
                subdivisionsX=6
            )
            for layer, (offset, width) in enumerate(((height * .68, .48),
                                                     (height * 1.03, .34))):
                make(
                    cmds.polyCone, "islet_tree_%02d_crown_%02d" % (index, layer),
                    (tree_x, y + offset, tree_z),
                    (width, .27, width),
                    leaves if layer == 0 else light_leaves, islet_group,
                    rotate=(0, rng.uniform(0, 360), 0), subdivisionsX=6
                )
            if season() == "Winter":
                make(
                    cmds.polySphere, "islet_tree_%02d_snow" % index,
                    (tree_x, y + height * 1.28, tree_z),
                    (.34, .065, .29), snow, islet_group,
                    subdivisionsX=7, subdivisionsY=4
                )


def terrain_detail_count():
    if cmds.control("detailSlider", exists=True):
        return (140, 320, 560)[cmds.intSliderGrp(
            "detailSlider", query=True, value=True
        ) - 1]
    return 320


def water_feature():
    return CURRENT_WATER_FEATURE


def set_water_feature(value, rebuild=True):
    """Lake/River/None uses the same clear button pattern as seasons."""
    global CURRENT_WATER_FEATURE
    CURRENT_WATER_FEATURE = value
    if cmds.control("waterReadout", exists=True):
        cmds.text(
            "waterReadout", edit=True,
            label="WATER FEATURE  ·  %s" % value.upper()
        )
    if rebuild and cmds.objExists(ROOT):
        with undo_chunk("Change island water feature"):
            create_environment()
            _apply_time_of_day()


def water_size():
    if cmds.control("waterSizeSlider", exists=True):
        return cmds.floatSliderGrp(
            "waterSizeSlider", query=True, value=True
        )
    return 1.0


def water_surface_y(x, z):
    """A tiny offset prevents z-fighting while keeping water on the ground."""
    return ground_contact_y(x, z) + .026


def create_lake(parent, mats, size):
    """An irregular triangulated lake, sampled directly from the terrain."""
    rng = random.Random(world_seed() * 197 + 31)
    base_x, base_z = 3.0, -5.0
    center_x, center_z = world_xz(base_x, base_z)
    vertices = [(center_x, water_surface_y(center_x, center_z), center_z)]
    shoreline = []
    count = 15

    for index in range(count):
        angle = math.tau * index / count
        radius_x = (2.65 + rng.uniform(-.40, .45)) * size
        radius_z = (1.78 + rng.uniform(-.28, .35)) * size
        px, pz = world_xz(
            base_x + math.cos(angle) * radius_x,
            base_z + math.sin(angle) * radius_z
        )
        shoreline.append((px, pz))
        vertices.append((px, water_surface_y(px, pz), pz))

    # Reversed winding gives the surface upward-facing normals, so Maya's
    # viewport lights it blue instead of shading the underside black.
    faces = [
        (0, ((index + 1) % count) + 1, index + 1)
        for index in range(count)
    ]
    make_mesh("island_lake_conforming", vertices, faces, mats["water"], parent)

    # A few reeds and banks break the perfect outline without making a rim float.
    for index, (px, pz) in enumerate(shoreline):
        if index % 2:
            continue
        py = ground_contact_y(px, pz)
        make(
            cmds.polyCylinder, "lake_reed_%02d" % index,
            (px, py + .24, pz), (.04, .24, .04), mats["reed"], parent,
            rotate=(0, index * 31, 0), subdivisionsX=5
        )
        if index % 4 == 0:
            make(
                cmds.polySphere, "lake_bank_rock_%02d" % index,
                (px, py + .09, pz), (.28, .15, .22), mats["blue_rock"], parent,
                rotate=(0, index * 29, 0), subdivisionsX=6, subdivisionsY=4
            )


def river_base_point(amount):
    """Follow the crescent's low valley instead of crossing its open sea bay."""
    position = max(0.0, min(1.0, amount)) * (len(RIVER_ROUTE) - 1)
    segment = min(int(position), len(RIVER_ROUTE) - 2)
    blend = position - segment
    blend = blend * blend * (3.0 - 2.0 * blend)
    start, end = RIVER_ROUTE[segment], RIVER_ROUTE[segment + 1]
    return (
        lerp(start[0], end[0], blend),
        lerp(start[1], end[1], blend),
    )


def create_river(parent, mats, size):
    """One shared-vertex strip, so a river cannot turn into visible stair blocks."""
    sections = 36
    scale = (island_width() + island_depth()) * .5
    vertices, banks = [], []

    for index in range(sections):
        amount = index / float(sections - 1)
        base_x, base_z = river_base_point(amount)
        before = river_base_point(max(0.0, amount - .012))
        after = river_base_point(min(1.0, amount + .012))
        center_x, center_z = world_xz(base_x, base_z)
        before_x, before_z = world_xz(*before)
        after_x, after_z = world_xz(*after)
        tangent_x, tangent_z = after_x - before_x, after_z - before_z
        length = max(.001, math.sqrt(tangent_x * tangent_x + tangent_z * tangent_z))
        normal_x, normal_z = -tangent_z / length, tangent_x / length
        half_width = (
            .46 + math.sin(amount * math.pi * 5.0) * .10
        ) * size * scale
        left_x, left_z = center_x + normal_x * half_width, center_z + normal_z * half_width
        right_x, right_z = center_x - normal_x * half_width, center_z - normal_z * half_width
        vertices.extend((
            (left_x, water_surface_y(left_x, left_z), left_z),
            (right_x, water_surface_y(right_x, right_z), right_z),
        ))
        banks.append(((left_x, left_z), (right_x, right_z)))

    faces = [
        (index * 2, index * 2 + 2, index * 2 + 3, index * 2 + 1)
        for index in range(sections - 1)
    ]
    make_mesh("island_river_conforming", vertices, faces, mats["water"], parent)

    # Only selected river bends gain rocks: it feels natural without a hard edge.
    for index in range(2, sections - 2, 5):
        for side, (px, pz) in enumerate(banks[index]):
            py = ground_contact_y(px, pz)
            make(
                cmds.polySphere, "river_bank_%02d_%d" % (index, side),
                (px, py + .08, pz), (.24, .13, .18), mats["deep_rock"], parent,
                rotate=(0, index * 37 + side * 51, 0),
                subdivisionsX=6, subdivisionsY=4
            )


def create_winter_ice(parent, feature, size):
    """Small irregular floes rest just above the water surface in winter."""
    if season() != "Winter":
        return

    rng = random.Random(world_seed() * 821 + (11 if feature == "Lake" else 23))
    ice = material("island_water_ice", (.73, .88, .94))

    def floe(index, x, z, scale):
        make(
            cmds.polyCylinder, "winter_ice_%s_%02d" % (feature.lower(), index),
            (x, water_surface_y(x, z) + .024, z),
            (scale, .022, scale * rng.uniform(.55, .92)), ice, parent,
            rotate=(0, rng.uniform(0, 360), 0), subdivisionsX=rng.choice((5, 6, 7))
        )

    if feature == "Lake":
        for index in range(13):
            while True:
                offset_x = rng.uniform(-2.10, 2.10) * size
                offset_z = rng.uniform(-1.28, 1.28) * size
                if (offset_x / (2.18 * size)) ** 2 + (offset_z / (1.34 * size)) ** 2 < .82:
                    break
            x, z = world_xz(3.0 + offset_x, -5.0 + offset_z)
            floe(index, x, z, rng.uniform(.16, .38))
        return

    scale = (island_width() + island_depth()) * .5
    for index in range(15):
        amount = rng.uniform(.08, .92)
        base_x, base_z = river_base_point(amount)
        before = river_base_point(max(0.0, amount - .012))
        after = river_base_point(min(1.0, amount + .012))
        x, z = world_xz(base_x, base_z)
        before_x, before_z = world_xz(*before)
        after_x, after_z = world_xz(*after)
        tangent_x, tangent_z = after_x - before_x, after_z - before_z
        length = max(.001, math.sqrt(tangent_x * tangent_x + tangent_z * tangent_z))
        normal_x, normal_z = -tangent_z / length, tangent_x / length
        offset = rng.uniform(-.25, .25) * size * scale
        floe(index, x + normal_x * offset, z + normal_z * offset,
             rng.uniform(.11, .23) * scale)


def create_water_feature(parent, mats):
    """Water is a terrain-conforming mesh, never a floating cylinder or cubes."""
    feature = water_feature()
    if feature == "None":
        return
    if feature == "Lake":
        create_lake(parent, mats, water_size())
    else:
        create_river(parent, mats, water_size())
    create_winter_ice(parent, feature, water_size())


def create_path_strip(parent, mats, name, start, end, bend, width, sections=24):
    """Lay a shared-vertex gravel path directly on the uneven terrain."""
    def sample(amount):
        return (
            start[0] * (1.0 - amount) + end[0] * amount +
            math.sin(amount * math.pi) * bend[0],
            start[1] * (1.0 - amount) + end[1] * amount +
            math.sin(amount * math.pi) * bend[1],
        )

    vertices, centers = [], []
    path_width = width * (island_width() + island_depth()) * .5
    for index in range(sections):
        amount = index / float(sections - 1)
        base_x, base_z = sample(amount)
        before = sample(max(0.0, amount - .015))
        after = sample(min(1.0, amount + .015))
        x, z = world_xz(base_x, base_z)
        before_x, before_z = world_xz(*before)
        after_x, after_z = world_xz(*after)
        tangent_x, tangent_z = after_x - before_x, after_z - before_z
        length = max(.001, math.sqrt(tangent_x * tangent_x + tangent_z * tangent_z))
        normal_x, normal_z = -tangent_z / length, tangent_x / length
        left_x, left_z = x + normal_x * path_width, z + normal_z * path_width
        right_x, right_z = x - normal_x * path_width, z - normal_z * path_width
        vertices.extend((
            (left_x, ground_contact_y(left_x, left_z) + .018, left_z),
            (right_x, ground_contact_y(right_x, right_z) + .018, right_z),
        ))
        centers.append((x, z, math.degrees(math.atan2(tangent_x, tangent_z))))

    faces = [
        (index * 2, index * 2 + 2, index * 2 + 3, index * 2 + 1)
        for index in range(sections - 1)
    ]
    make_mesh(name + "_strip", vertices, faces, mats["path"], parent)

    # Scattered flat stones keep the route handmade and readable in low poly.
    rng = random.Random(world_seed() * 607 + len(name))
    pebble = material("path_pebble", (.48, .38, .30))
    for index in range(2, sections - 2, 3):
        x, z, heading = centers[index]
        y = ground_contact_y(x, z) + .032
        make(
            cmds.polyCylinder, "%s_paver_%02d" % (name, index), (x, y, z),
            (path_width * rng.uniform(.42, .68), .014,
             path_width * rng.uniform(.38, .58)), pebble, parent,
            rotate=(0, heading + rng.uniform(-17, 17), 0), subdivisionsX=6
        )


def create_village_path(parent, mats):
    """A small road network makes the settlement feel lived in, not arranged."""
    village = VILLAGE_SITE
    create_path_strip(
        parent, mats, "castle_road", CASTLE_SITE, village, (1.18, .65), .27, 28
    )
    create_path_strip(
        parent, mats, "house_lane", village, (5.5, 3.3), (-.52, .42), .19, 16
    )
    create_path_strip(
        parent, mats, "meadow_track", village, (-1.8, 6.4), (.30, -.18), .16, 15
    )

    # A few grounded lanterns establish a cared-for route after dark.
    wood = material("path_lantern_wood", (.20, .11, .07))
    glow = material("path_lantern_glow", (1.0, .65, .24))
    for index, (base_x, base_z) in enumerate(((-3.8, 4.0), (-.4, 4.6), (3.0, 4.3))):
        x, z = world_xz(base_x, base_z)
        y = ground_contact_y(x, z)
        make(cmds.polyCylinder, "path_lantern_post_%02d" % index,
             (x, y + .34, z), (.045, .34, .045), wood, parent, subdivisionsX=5)
        make(cmds.polySphere, "path_lantern_light_%02d" % index,
             (x, y + .72, z), (.11, .11, .11), glow, parent,
             subdivisionsX=6, subdivisionsY=4)


def create_ground_details(parent, mats):
    """Seasonal low-poly details make the ground, not just trees, change."""
    palette = SEASONS[season()]
    count = max(36, terrain_detail_count() // 5)
    seed = {"Spring": 17, "Summer": 31, "Autumn": 47, "Winter": 63}[season()]
    rng = random.Random(world_seed() + seed)

    if season() == "Winter":
        # Large uneven blankets make winter visually different from every other season.
        for patch in range(28):
            while True:
                base_x = rng.uniform(-13.0, 13.0)
                base_z = rng.uniform(-10.5, 10.5)
                test_x, test_z = world_xz(base_x, base_z)
                if is_on_island(test_x, test_z):
                    break
            x, z = world_xz(base_x, base_z)
            y = ground_contact_y(x, z) + .035
            width = rng.uniform(.55, 1.65)
            make(
                cmds.polySphere, "winter_snow_patch_%02d" % patch, (x, y, z),
                (width * island_width(), rng.uniform(.045, .11),
                 width * island_depth() * rng.uniform(.55, 1.15)),
                mats["snow"], parent, rotate=(0, rng.uniform(0, 360), 0),
                subdivisionsX=7, subdivisionsY=4
            )

    for index in range(count):
        while True:
            base_x, base_z = rng.uniform(-13.2, 13.2), rng.uniform(-10.8, 10.8)
            x, z = world_xz(base_x, base_z)
            if is_on_island(x, z):
                break
        y = ground_contact_y(x, z) + .055

        if season() == "Winter":
            scale = rng.uniform(.10, .24)
            make(
                cmds.polySphere, "winter_snow_%03d" % index, (x, y, z),
                (scale, scale * .20, scale * .75), mats["snow"], parent,
                rotate=(0, rng.uniform(0, 360), 0),
                subdivisionsX=6, subdivisionsY=4
            )
        elif season() == "Autumn":
            scale = rng.uniform(.07, .15)
            make(
                cmds.polySphere, "autumn_leaf_%03d" % index, (x, y, z),
                (scale * 1.4, .025, scale), mats["detail"], parent,
                rotate=(0, rng.uniform(0, 360), 0),
                subdivisionsX=6, subdivisionsY=4
            )
        elif season() == "Spring":
            flower_size = rng.uniform(.035, .075)
            for petal in range(5):
                angle = petal * math.pi * 2.0 / 5.0
                make(
                    cmds.polySphere,
                    "spring_flower_%03d_%02d" % (index, petal),
                    (x + math.cos(angle) * flower_size * 1.25,
                     y + .018,
                     z + math.sin(angle) * flower_size * 1.25),
                    (flower_size, flower_size * .32, flower_size),
                    mats["detail"], parent,
                    rotate=(0, angle * 57.3, 0),
                    subdivisionsX=5, subdivisionsY=4
                )
        else:
            scale = rng.uniform(.045, .10)
            make(
                cmds.polySphere, "summer_grass_%03d" % index, (x, y, z),
                (scale, scale * .24, scale), mats["detail"], parent,
                subdivisionsX=6, subdivisionsY=4
            )


def create_surface_fragments(parent, mats):
    """Des centaines de facettes petites: le corps n'est plus une grosse sphere lisse."""
    rng = random.Random(world_seed() + 20260915)
    shades = (mats["deep_rock"], mats["blue_rock"],
              mats["violet_rock"], mats["lavender_rock"])
    for index in range(terrain_detail_count()):
        while True:
            base_x, base_z = rng.uniform(-13.8, 13.8), rng.uniform(-11.4, 11.4)
            world_x, world_z = world_xz(base_x, base_z)
            if is_on_island(world_x, world_z):
                break
        size = rng.uniform(.12, .48)
        make(cmds.polySphere, "island_facet_%03d" % index,
             (world_x, ground_contact_y(world_x, world_z) - rng.uniform(.04, .20), world_z),
             (size * island_width(), size * rng.uniform(.18, .50),
              size * island_depth() * rng.uniform(.55, 1.5)),
             shades[index % len(shades)], parent,
             (rng.uniform(0, 65), rng.uniform(0, 360), rng.uniform(0, 65)),
             subdivisionsX=6, subdivisionsY=4)


def create_castle(parent, mats):
    """An off-centre but internally centred castle, rooted to its cliff."""
    center_x, center_z = world_xz(*CASTLE_SITE)
    # All pieces are built at this exact world-space site.  The older version
    # moved the parent after building local pieces, which left the castle apart
    # from its plinth.  Keeping the group at origin prevents that offset.
    cmds.xform(parent, worldSpace=True, translation=(0, 0, 0))
    summit = ground_contact_y(center_x, center_z)

    def location(local_x, local_z):
        return center_x + local_x, center_z + local_z

    # A rock plinth touches the cliff. The stone foundation then sits directly
    # on that plinth, so towers, walls, and the castle read as one structure.
    terrace_y = summit - .55
    make(cmds.polyCylinder, "castle_cliff_terrace", (center_x, terrace_y, center_z),
         (3.35, .55, 2.85), mats["violet_rock"], parent, subdivisionsX=9)

    foundation_y = summit + .24
    make(cmds.polyCylinder, "castle_foundation", (center_x, foundation_y, center_z),
         (2.30, .24, 2.05), mats["castle_stone"], parent, subdivisionsX=10)
    base = summit + .48

    walls = [
        (0, -1.35, 1.18, .58, .14), (0, 1.78, 1.18, .58, .14),
        (-1.95, .20, .14, .58, 1.55), (1.95, .20, .14, .58, 1.55),
    ]
    for index, (local_x, local_z, sx, sy, sz) in enumerate(walls):
        x, z = location(local_x, local_z)
        make(cmds.polyCube, "castle_wall_%02d" % index, (x, base + sy / 2.0, z),
             (sx, sy, sz), mats["castle_stone"], parent)
        for tooth in range(-3, 4):
            if index < 2:
                px, pz = location(local_x + tooth * .30, local_z)
            else:
                px, pz = location(local_x, local_z + tooth * .30)
            make(cmds.polyCube, "castle_merlon_%02d_%02d" % (index, tooth + 3),
                 (px, base + sy + .065, pz), (.09, .14, .09),
                 mats["castle_stone"], parent)

    towers = [(-1.95, -1.35, 2.25), (1.95, -1.35, 2.65),
              (-1.95, 1.78, 2.45), (1.95, 1.78, 2.15), (0, .45, 3.65)]
    snow = material("castle_snow", SEASONS["Winter"]["snow_light"])
    for index, (local_x, local_z, height) in enumerate(towers):
        x, z = location(local_x, local_z)
        make(cmds.polyCylinder, "castle_tower_%02d" % index,
             (x, base + height / 2.0, z), (.42, height / 2.0, .42),
             mats["castle_stone"], parent, subdivisionsX=8)
        if index in (0, 3):
            for tooth in range(8):
                angle = tooth * math.pi * 2.0 / 8.0
                make(cmds.polyCube, "castle_tower_tooth_%02d_%02d" % (index, tooth),
                     (x + math.cos(angle) * .36, base + height + .060,
                      z + math.sin(angle) * .36), (.08, .13, .08),
                     mats["castle_stone"], parent)
        else:
            roof_y = base + height + .46
            make(cmds.polyCone, "castle_roof_%02d" % index,
                 (x, roof_y, z), (.62, .58, .62),
                 mats["castle_dark"], parent, subdivisionsX=8)
            if season() == "Winter":
                make(cmds.polyCone, "castle_roof_snow_%02d" % index,
                     (x, roof_y + .55, z), (.54, .055, .54), snow, parent,
                     subdivisionsX=8)

    keep_x, keep_z = location(0, .45)
    make(cmds.polyCube, "castle_keep", (keep_x, base + .91, keep_z),
         (.75, 1.82, .66), mats["castle_stone"], parent)
    make(cmds.polyCone, "castle_keep_roof", (keep_x, base + 2.47, keep_z),
         (1.03, .72, .88), mats["castle_dark"], parent, subdivisionsX=4)
    if season() == "Winter":
        make(cmds.polyCone, "castle_keep_roof_snow", (keep_x, base + 3.14, keep_z),
             (.92, .060, .78), snow, parent, subdivisionsX=4)
    gate_x, gate_z = location(0, -1.50)
    make(cmds.polyCube, "castle_gate", (gate_x, base + .20, gate_z),
         (.30, .40, .04), mats["castle_dark"], parent)
    for local_x in (-.48, .48):
        timber_x, timber_z = location(local_x, -1.47)
        make(cmds.polyCube, "castle_timber_%s" % str(local_x).replace("-", "n"),
             (timber_x, base + .88, timber_z), (.07, 1.76, .03),
             mats["castle_wood"], parent)



def create_sky(parent, mats):
    """Create stars, moon, and a visible sun that time-of-day can move."""
    clear_group(parent)
    stars = cmds.group(empty=True, name="island_stars_GRP", parent=parent)
    rng = random.Random(2406)

    for index in range(72):
        base_x = rng.uniform(-24, 24)
        base_z = rng.uniform(-18, 18)
        x, z = world_xz(base_x, base_z)
        y = rng.uniform(14, 25)
        size = rng.uniform(.035, .09)
        make(
            cmds.polySphere, "sky_star_%02d" % index, (x, y, z),
            (size, size, size), mats["star"], stars,
            subdivisionsX=5, subdivisionsY=4
        )

    moon_x, moon_z = world_xz(-12, -10)
    moon = glow_material("island_moon", (.70, .80, 1.0), .42)
    make(
        cmds.polySphere, "sky_moon", (moon_x, 19, moon_z),
        (.96, .96, .96), moon, stars,
        subdivisionsX=8, subdivisionsY=6
    )
    sun = glow_material("island_sun_disc", (1.0, .78, .42), .45)
    make(
        cmds.polySphere, "sky_sun", (0, 19, -16),
        (.82, .82, .82), sun, parent,
        subdivisionsX=9, subdivisionsY=7
    )


def create_ocean_reflections(parent):
    """Broken low-poly shimmer strips rest on the actual ocean surface."""
    sun_glitter = glow_material("ocean_sun_glitter", (1.0, .73, .34), .58)
    moon_glitter = glow_material("ocean_moon_glitter", (.62, .77, 1.0), .34)
    sun_group = cmds.group(
        empty=True, name="island_sun_reflection_GRP", parent=parent
    )
    moon_group = cmds.group(
        empty=True, name="island_moon_reflection_GRP", parent=parent
    )
    rng = random.Random(world_seed() * 911 + 5)

    for index in range(28):
        amount = index / 27.0
        make(
            cmds.polyCube, "ocean_sun_glitter_%02d" % index,
            (rng.uniform(-.34, .34) * (1.0 + amount), -.284,
             -18.0 + amount * 27.0),
            (.32 + amount * 1.45, .018, .055 + amount * .16),
            sun_glitter, sun_group,
            rotate=(0, rng.uniform(-7, 7), 0)
        )

    for index in range(15):
        amount = index / 14.0
        make(
            cmds.polyCube, "ocean_moon_glitter_%02d" % index,
            (rng.uniform(-.22, .22), -.282, -15.0 + amount * 16.0),
            (.16 + amount * .58, .014, .04 + amount * .10),
            moon_glitter, moon_group,
            rotate=(0, rng.uniform(-6, 6), 0)
        )

def create_environment():
    global TERRAIN_SURFACES
    TERRAIN_SURFACES = []

    parent = GROUPS["environment"]
    castle_parent = GROUPS["castle"]
    sky_parent = GROUPS["sky"]
    cmds.setAttr(sky_parent + ".visibility", True)
    clear_group(parent)
    clear_group(castle_parent)
    clear_group(sky_parent)
    mats = make_materials()

    make(
        cmds.polyCylinder, "island_ocean", (0, -.60, 0),
        (160, .30, 160), mats["ocean"], parent, subdivisionsX=96
    )
    create_ocean_reflections(parent)

    land_shades = (mats["deep_rock"], mats["blue_rock"], mats["violet_rock"],
                   mats["lavender_rock"])
    parts = [
        (cx, cy, cz, sx, sy, sz, land_shades[index % len(land_shades)], (0, 0, 0))
        for index, (cx, cy, cz, sx, sy, sz) in enumerate(LAND_FORMS)
    ]

    for index, data in enumerate(parts):
        mountain(parent, index, data)

    caps = [
        (-7.0, 4.2, 7.20, 2.2, .28, 2.0, mats["snow"], (0, 22, -30)),
        (-2.5, 6.2, 5.75, 2.4, .30, 2.0, mats["snow_light"], (0, -18, 28)),
        (2.1, 5.1, 4.70, 1.9, .26, 1.8, mats["snow"], (0, -15, 42)),
        (3.1, -5.4, 4.95, 1.8, .25, 1.6, mats["snow_light"], (0, 14, 0)),
    ]

    if season() == "Winter":
        for index, cap in enumerate(caps):
            snow_cap(parent, index, *cap)

    create_beaches(parent, mats)
    create_side_islet_details(parent, mats)
    create_surface_fragments(parent, mats)
    create_shore_rocks(parent, mats)
    create_water_feature(parent, mats)
    create_village_path(parent, mats)
    create_ground_details(parent, mats)
    create_castle(castle_parent, mats)
    create_sky(sky_parent, mats)


def add_tree_snow(parent, x, y, z, width):
    if season() != "Winter":
        return
    snow = material("tree_snow", (1.0, .88, .86))
    make(cmds.polySphere, "tree_snow", (x, y, z),
         (width, .12, width * .82), snow, parent,
         subdivisionsX=8, subdivisionsY=5)


def create_single_tree(index, point):
    """Build one tree; create_tree decides whether it belongs to a mini-forest."""
    base_x, base_z = organic_point(point, index, .22)
    x, z = world_xz(base_x, base_z)
    y = ground_contact_y(x, z)
    parent = cmds.group(empty=True, name="island_tree_%02d_GRP" % index,
                        parent=GROUPS["trees"])
    rng = random.Random(world_seed() * 29 + index * 313)
    trunk = material("tree_trunk", (.19, .06, .08))
    birch = material("tree_birch_trunk", (.67, .57, .47))
    leaves = material("tree_foliage", SEASONS[season()]["leaf"])
    light_leaf = material(
        "tree_foliage_light",
        tuple(min(1.0, component * 1.35 + .04) for component in SEASONS[season()]["leaf"])
    )
    dark_leaf = material(
        "tree_foliage_dark",
        tuple(component * .62 for component in SEASONS[season()]["leaf"])
    )
    height = rng.uniform(1.45, 2.65)
    style = rng.choice(("pine", "pine", "oak", "birch", "wind_bent"))

    if style == "pine":
        make(cmds.polyCylinder, "tree_%02d_trunk" % index,
             (x, y + height / 2.0, z), (.13, height / 2.0, .13), trunk,
             parent, subdivisionsX=6)
        layers = ((height * .72, 1.00), (height + .42, .72),
                  (height + .96, .42))
        for layer, (offset, width) in enumerate(layers):
            make(cmds.polyCone, "tree_%02d_pine_%02d" % (index, layer),
                 (x, y + offset, z), (width, .66, width), leaves, parent,
                 rotate=(0, rng.uniform(-16, 16), 0), subdivisionsX=6)
            add_tree_snow(parent, x, y + offset + .38, z, width * .80)

    elif style == "oak":
        make(cmds.polyCylinder, "tree_%02d_trunk" % index,
             (x, y + height * .48, z), (.17, height * .48, .17), trunk,
             parent, subdivisionsX=7)
        for branch, direction in enumerate((-32, 34)):
            make(cmds.polyCylinder, "tree_%02d_branch_%02d" % (index, branch),
                 (x + direction / 160.0, y + height * .88, z),
                 (.09, .52, .09), trunk, parent,
                 rotate=(0, 0, direction), subdivisionsX=6)
        for crown in range(4):
            angle = crown * math.tau / 4.0 + rng.uniform(-.25, .25)
            px = x + math.cos(angle) * rng.uniform(.20, .52)
            pz = z + math.sin(angle) * rng.uniform(.20, .48)
            py = y + height + rng.uniform(.05, .45)
            width = rng.uniform(.52, .74)
            make(cmds.polySphere, "tree_%02d_oak_%02d" % (index, crown),
                 (px, py, pz), (width, width * .70, width),
                 light_leaf if crown % 2 else leaves, parent,
                 subdivisionsX=7, subdivisionsY=5)
            add_tree_snow(parent, px, py + width * .48, pz, width * .72)

    elif style == "birch":
        make(cmds.polyCylinder, "tree_%02d_birch_trunk" % index,
             (x, y + height * .50, z), (.105, height * .50, .105), birch,
             parent, subdivisionsX=6)
        for crown, offset in enumerate(((-.28, .08), (.24, -.05), (.02, .28))):
            px, pz = x + offset[0], z + offset[1]
            py = y + height * .92 + crown * .28
            make(cmds.polySphere, "tree_%02d_birch_leaf_%02d" % (index, crown),
                 (px, py, pz), (.50, .42, .45), light_leaf, parent,
                 subdivisionsX=7, subdivisionsY=5)
            add_tree_snow(parent, px, py + .29, pz, .40)

    else:  # A vertical rooted trunk plus a bent upper branch reads as wind-shaped.
        make(cmds.polyCylinder, "tree_%02d_rooted_trunk" % index,
             (x, y + height * .34, z), (.15, height * .34, .15), trunk,
             parent, subdivisionsX=6)
        lean = rng.choice((-34, 34))
        make(cmds.polyCylinder, "tree_%02d_wind_branch" % index,
             (x + lean / 140.0, y + height * .78, z),
             (.115, height * .38, .115), trunk, parent,
             rotate=(0, 0, lean), subdivisionsX=6)
        for crown in range(3):
            px = x + (lean / 105.0) + crown * (lean / 400.0)
            pz = z + rng.uniform(-.25, .25)
            py = y + height + .10 + crown * .25
            make(cmds.polySphere, "tree_%02d_wind_leaf_%02d" % (index, crown),
                 (px, py, pz), (.56, .40, .48), dark_leaf, parent,
                 subdivisionsX=7, subdivisionsY=5)
            add_tree_snow(parent, px, py + .26, pz, .43)


def create_tree(index, point):
    """Mix lone trees with tiny, deliberately spaced forest clusters."""
    rng = random.Random(world_seed() * 733 + index * 59)
    if index % 7 == 0:
        offsets = ((-1.25, -.55), (1.25, -.45), (0.0, 1.55))
    elif index % 4 == 1:
        offsets = ((-1.10, -.30), (1.10, .34))
    else:
        offsets = ((0.0, 0.0),)

    made_tree = False
    for member, (offset_x, offset_z) in enumerate(offsets):
        candidate = (point[0] + offset_x, point[1] + offset_z)
        world_x, world_z = world_xz(*candidate)
        # 2.2+ map units between stems prevents the crown meshes touching.
        if is_on_island(world_x, world_z):
            create_single_tree(index * 4 + member, candidate)
            made_tree = True
    if not made_tree:
        # A border point can reject its cluster children; it still receives one
        # grounded lone tree rather than placing foliage above the ocean.
        create_single_tree(index * 4, point)


def create_house(index, point):
    """Build a village with cottages, round homes, towers, and longhouses."""
    base_x, base_z = organic_point(point, index, .30)
    x, z = world_xz(base_x, base_z)
    y = ground_contact_y(x, z)
    parent = cmds.group(empty=True, name="island_house_%02d_GRP" % index,
                        parent=GROUPS["houses"])
    rng = random.Random(world_seed() * 47 + index * 211)
    # Homes are deliberately smaller than the forest silhouettes around them.
    size = rng.uniform(.52, .78)
    wall = material("house_wall_%02d" % index,
                    rng.choice(((.66, .44, .42), (.73, .55, .45),
                                (.48, .49, .62), (.43, .58, .48))))
    roof = material("house_roof_%02d" % index,
                    rng.choice(((.15, .08, .12), (.26, .10, .13),
                                (.16, .18, .28), (.22, .15, .08))))
    wood = material("house_wood", (.23, .10, .08))
    roof_snow = material("house_roof_snow", SEASONS["Winter"]["snow"])
    style = rng.choice(("cottage", "round", "tower", "longhouse"))

    if style == "cottage":
        make(cmds.polyCube, "house_%02d_cottage_body" % index,
             (x, y + size * .35, z), (size, size * .70, size * .78), wall, parent)
        make(cmds.polyCone, "house_%02d_cottage_roof" % index,
             (x, y + size * 1.24, z), (size * 1.34, size * .62, size * 1.10),
             roof, parent, (0, 45, 0), subdivisionsX=4)
        if season() == "Winter":
            make(cmds.polyCone, "house_%02d_cottage_snow" % index,
                 (x, y + size * 1.82, z), (size * 1.28, size * .11, size * 1.05),
                 roof_snow, parent, (0, 45, 0), subdivisionsX=4)
        door_z = z + size * .80

    elif style == "round":
        make(cmds.polyCylinder, "house_%02d_round_body" % index,
             (x, y + size * .58, z), (size * .78, size * .58, size * .78), wall,
             parent, subdivisionsX=8)
        make(cmds.polyCone, "house_%02d_round_roof" % index,
             (x, y + size * 1.45, z), (size * 1.10, size * .62, size * 1.10),
             roof, parent, subdivisionsX=8)
        if season() == "Winter":
            make(cmds.polyCone, "house_%02d_round_snow" % index,
                 (x, y + size * 2.12, z), (size, size * .10, size), roof_snow,
                 parent, subdivisionsX=8)
        door_z = z + size * .76

    elif style == "tower":
        make(cmds.polyCube, "house_%02d_tower_body" % index,
             (x, y + size * .51, z), (size * .62, size * 1.02, size * .62), wall,
             parent)
        make(cmds.polyCone, "house_%02d_tower_roof" % index,
             (x, y + size * 1.64, z), (size * .92, size * .70, size * .92), roof,
             parent, (0, 45, 0), subdivisionsX=4)
        if season() == "Winter":
            make(cmds.polyCone, "house_%02d_tower_snow" % index,
                 (x, y + size * 2.26, z), (size * .84, size * .10, size * .84),
                 roof_snow, parent, (0, 45, 0), subdivisionsX=4)
        door_z = z + size * .65

    else:
        make(cmds.polyCube, "house_%02d_long_body" % index,
             (x, y + size * .29, z), (size * 1.30, size * .58, size * .62), wall,
             parent)
        make(cmds.polyCone, "house_%02d_long_roof" % index,
             (x, y + size * 1.04, z), (size * 1.55, size * .54, size * .88), roof,
             parent, (0, 45, 0), subdivisionsX=4)
        if season() == "Winter":
            make(cmds.polyCone, "house_%02d_long_snow" % index,
                 (x, y + size * 1.52, z), (size * 1.45, size * .10, size * .80),
                 roof_snow, parent, (0, 45, 0), subdivisionsX=4)
        door_z = z + size * .66

    make(cmds.polyCube, "house_%02d_door" % index,
         (x, y + size * .16, door_z), (size * .20, size * .32, .035),
         wood, parent)


def create_cloud(index):
    parent = cmds.group(empty=True, name="island_cloud_%02d_GRP" % index,
                        parent=GROUPS["clouds"])
    cloud = material("cloud_cream", (.98, .86, .83))
    rng = random.Random(world_seed() * 71 + index)
    base_x = rng.uniform(-19, 19)
    base_z = rng.uniform(-12, 12)
    x, z = world_xz(base_x, base_z)
    y = rng.uniform(11, 18)
    for part in range(rng.randint(3, 6)):
        make(cmds.polySphere, "cloud_%02d_%02d" % (index, part),
             (x + (part - 2) * rng.uniform(.5, 1.05),
              y + rng.uniform(-.25, .35), z),
             (rng.uniform(.55, 1.25),
              rng.uniform(.28, .62),
              rng.uniform(.45, .88)),
             cloud, parent, subdivisionsX=8, subdivisionsY=5)


def create_weather():
    """Make visible, lightly animated weather under its own safe group."""
    parent = GROUPS["weather"]
    clear_group(parent)
    if weather() == "Clear":
        return

    rng = random.Random(world_seed() * 389 + (1 if weather() == "Rain" else 2))
    cloud = material("weather_cloud", (.48, .53, .63))
    rain = material("weather_rain", (.30, .62, .90))
    snow = material("weather_snow", (1.0, .98, .96))

    # Three dedicated storm clouds make precipitation readable even with zero
    # decorative clouds selected in Island Life.
    for cloud_index in range(3):
        base_x = -7.0 + cloud_index * 7.0 + rng.uniform(-1.2, 1.2)
        base_z = rng.uniform(-5.0, 6.5)
        x, z = world_xz(base_x, base_z)
        cloud_y = 15.5 + rng.uniform(-.8, .8)
        for part in range(3):
            make(
                cmds.polySphere, "weather_cloud_%02d_%02d" % (cloud_index, part),
                (x + (part - 1) * .72, cloud_y + rng.uniform(-.18, .20), z),
                (1.08, .42, .70), cloud, parent,
                subdivisionsX=7, subdivisionsY=5
            )

    count = 92 if weather() == "Rain" else 58
    start_frame = cmds.currentTime(query=True)
    for index in range(count):
        x, z = world_xz(rng.uniform(-13.5, 13.5), rng.uniform(-9.5, 9.5))
        ground = ground_contact_y(x, z)
        start_y = max(ground + 5.0, rng.uniform(8.0, 16.0))
        end_y = ground + .18
        if weather() == "Rain":
            node = make(
                cmds.polyCylinder, "weather_rain_%03d" % index,
                (x, start_y, z), (.018, .32, .018), rain, parent,
                rotate=(rng.uniform(-8, 8), 0, rng.uniform(-8, 8)),
                subdivisionsX=5
            )
            end_frame = start_frame + rng.randint(16, 28)
        else:
            node = make(
                cmds.polySphere, "weather_snow_%03d" % index,
                (x, start_y, z), (rng.uniform(.035, .085),) * 3, snow, parent,
                subdivisionsX=5, subdivisionsY=4
            )
            end_frame = start_frame + rng.randint(34, 58)

        cmds.setKeyframe(node, attribute="translateY", time=start_frame, value=start_y)
        cmds.setKeyframe(node, attribute="translateY", time=end_frame, value=end_y)
        cmds.setInfinity(node, attribute="translateY", pri="cycle", poi="cycle")


def create_sheep(index, point):
    """Each slider step creates a small flock, a mother/baby pair, or a loner."""
    base_x, base_z = organic_point(point, index, .58)
    parent = cmds.group(empty=True, name="island_sheep_flock_%02d_GRP" % index,
                        parent=GROUPS["sheep"])
    rng = random.Random(world_seed() * 89 + index * 173)
    wool, dark = material("sheep_wool", (.93, .82, .80)), material(
        "sheep_dark", (.12, .06, .08))

    def make_one_sheep(member, offset_x, offset_z, scale):
        x, z = world_xz(base_x + offset_x, base_z + offset_z)
        y = ground_contact_y(x, z)
        heading = rng.uniform(0, 360)
        forward_x = math.sin(math.radians(heading))
        forward_z = math.cos(math.radians(heading))
        body_y = .19 * scale
        make(cmds.polySphere, "sheep_%02d_%02d_body" % (index, member),
             (x, y + body_y, z), (.32 * scale, body_y, .22 * scale),
             wool, parent, rotate=(0, heading, 0), subdivisionsX=7, subdivisionsY=5)
        make(cmds.polySphere, "sheep_%02d_%02d_head" % (index, member),
             (x + forward_x * .29 * scale, y + .24 * scale,
              z + forward_z * .29 * scale), (.105 * scale, .105 * scale, .105 * scale),
             dark, parent, subdivisionsX=6, subdivisionsY=4)
        # Two legs are enough at this scale and make the animals read as sheep.
        for leg, side in enumerate((-.14, .14)):
            make(cmds.polyCylinder, "sheep_%02d_%02d_leg_%d" % (index, member, leg),
                 (x + side * scale, y + .07 * scale, z),
                 (.035 * scale, .07 * scale, .035 * scale), dark, parent,
                 subdivisionsX=5)

    flock_type = index % 4
    if flock_type == 0:  # a lone sheep, useful in open meadows
        make_one_sheep(0, 0, 0, rng.uniform(.88, 1.10))
    elif flock_type == 1:  # mother and a clearly smaller lamb
        make_one_sheep(0, -.14, .02, rng.uniform(1.0, 1.12))
        make_one_sheep(1, .31, -.15, rng.uniform(.48, .58))
    else:  # uneven little flocks, never a perfect row
        members = rng.choice((3, 3, 4))
        for member in range(members):
            make_one_sheep(
                member, rng.uniform(-.46, .46), rng.uniform(-.34, .34),
                rng.uniform(.76, 1.04)
            )




def create_villager(index, point):
    """Round-headed villagers appear alone, in pairs, or with a child."""
    base_x, base_z = organic_point(point, index, .26)
    parent = cmds.group(
        empty=True, name="island_villager_group_%02d_GRP" % index,
        parent=GROUPS["villagers"]
    )
    clothes = ((.72, .23, .30), (.24, .44, .68), (.61, .39, .18),
               (.41, .28, .53))
    skin = material("villager_skin", (.70, .44, .32))
    boot = material("villager_boot", (.10, .055, .045))
    hair_colours = ((.16, .075, .04), (.37, .18, .08), (.08, .07, .09))
    book = material("villager_book", (.20, .34, .57))
    flower = material("villager_flower", (.98, .42, .55))
    heart = glow_material("villager_heart", (1.0, .24, .42), .25)
    sparkle = glow_material("villager_sparkle", (1.0, .84, .30), .22)

    def make_person(member, offset_x, offset_z, scale):
        x, z = world_xz(base_x + offset_x, base_z + offset_z)
        y = ground_contact_y(x, z)
        shirt = material(
            "villager_shirt_%02d_%02d" % (index, member),
            clothes[(index + member) % len(clothes)]
        )
        hair = material(
            "villager_hair_%02d_%02d" % (index, member),
            hair_colours[(index * 2 + member) % len(hair_colours)]
        )
        make(
            cmds.polyCylinder, "villager_%02d_%02d_body" % (index, member),
            (x, y + .23 * scale, z), (.12 * scale, .23 * scale, .10 * scale),
            shirt, parent, subdivisionsX=6
        )
        # A sphere is intentionally the clearest silhouette: no pointed hat.
        make(
            cmds.polySphere, "villager_%02d_%02d_round_head" % (index, member),
            (x, y + .51 * scale, z), (.11 * scale, .11 * scale, .11 * scale),
            skin, parent, subdivisionsX=8, subdivisionsY=6
        )
        make(
            cmds.polySphere, "villager_%02d_%02d_hair" % (index, member),
            (x, y + .60 * scale, z), (.112 * scale, .035 * scale, .112 * scale),
            hair, parent, subdivisionsX=8, subdivisionsY=4
        )
        # Two tiny arms make the figures human instead of just walking hats.
        for arm, side in enumerate((-.16, .16)):
            make(
                cmds.polyCylinder, "villager_%02d_%02d_arm_%02d" % (index, member, arm),
                (x + side * scale, y + .29 * scale, z),
                (.032 * scale, .13 * scale, .032 * scale), shirt, parent,
                rotate=(0, 0, -72 if side < 0 else 72), subdivisionsX=5
            )
        held_x = x + .22 * scale
        if (index + member) % 4 == 0:
            make(
                cmds.polyCube, "villager_%02d_%02d_book" % (index, member),
                (held_x, y + .28 * scale, z + .05 * scale),
                (.09 * scale, .12 * scale, .030 * scale), book, parent,
                rotate=(0, 20, 0)
            )
        elif (index + member) % 4 == 1:
            make(
                cmds.polySphere, "villager_%02d_%02d_flower" % (index, member),
                (held_x, y + .39 * scale, z),
                (.055 * scale, .055 * scale, .035 * scale), flower, parent,
                subdivisionsX=6, subdivisionsY=4
            )
        for leg, side in enumerate((-.055, .055)):
            make(
                cmds.polyCube, "villager_%02d_%02d_boot_%02d" % (index, member, leg),
                (x + side * scale, y + .03 * scale, z),
                (.042 * scale, .06 * scale, .06 * scale), boot, parent
            )
        return x, y, z, scale

    def add_heart(first, second):
        x = (first[0] + second[0]) * .5
        z = (first[2] + second[2]) * .5
        y = max(first[1] + .82 * first[3], second[1] + .82 * second[3])
        make(cmds.polySphere, "villager_%02d_heart_left" % index,
             (x - .065, y + .055, z), (.075, .075, .045), heart, parent,
             subdivisionsX=6, subdivisionsY=4)
        make(cmds.polySphere, "villager_%02d_heart_right" % index,
             (x + .065, y + .055, z), (.075, .075, .045), heart, parent,
             subdivisionsX=6, subdivisionsY=4)
        make(cmds.polyCone, "villager_%02d_heart_tip" % index,
             (x, y - .030, z), (.115, .13, .075), heart, parent,
             rotate=(0, 0, 180), subdivisionsX=5)

    social_pattern = index % 5
    if social_pattern == 0:
        lone = make_person(0, 0, 0, 1.0)  # a quiet villager on their own
        make(cmds.polySphere, "villager_%02d_sparkle" % index,
             (lone[0], lone[1] + .82, lone[2]), (.045, .045, .045), sparkle, parent,
             subdivisionsX=5, subdivisionsY=4)
    elif social_pattern == 1:
        adult = make_person(0, -.22, .02, 1.0)
        child = make_person(1, .28, -.10, .60)  # adult and child
        add_heart(adult, child)
    elif social_pattern == 2:
        first = make_person(0, -.22, -.04, .96)
        second = make_person(1, .24, .08, .96)
        add_heart(first, second)
    else:
        first = make_person(0, -.28, -.12, .94)
        second = make_person(1, .28, -.02, .98)
        make_person(2, .02, .30, .62)  # a small family trio
        add_heart(first, second)


def create_monster(index, point):
    base_x, base_z = organic_point(point, index, .50)
    x, z = world_xz(base_x, base_z)
    y = ground_contact_y(x, z)
    parent = cmds.group(empty=True, name="island_monster_%02d_GRP" % index,
                        parent=GROUPS["monsters"])
    body = material("monster_body", (.018, .022, .032))
    horn = material("monster_horn", (.10, .12, .15))
    eye = material("monster_eye", (1.0, .42, .09))
    make(cmds.polySphere, "monster_%02d_body" % index,
         (x, y + .68, z), (.65, .68, .50),
         body, parent, subdivisionsX=8, subdivisionsY=5)
    for foot_index, (side_x, side_z) in enumerate(((-.30, -.20), (.30, -.20),
                                                     (-.30, .20), (.30, .20))):
        make(cmds.polyCylinder, "monster_%02d_foot_%d" % (index, foot_index),
             (x + side_x, y + .10, z + side_z), (.12, .10, .12), horn, parent,
             subdivisionsX=6)
    for horn_index, side in enumerate((-.28, .28)):
        make(cmds.polyCone, "monster_%02d_horn_%d" % (index, horn_index),
             (x + side, y + 1.55, z),
             (.16, .42, .16), horn, parent, subdivisionsX=6)
    for eye_index, side in enumerate((-.16, .16)):
        make(cmds.polySphere, "monster_%02d_eye_%d" % (index, eye_index),
             (x + side, y + .88, z + .46), (.045, .045, .035), eye, parent,
             subdivisionsX=5, subdivisionsY=4)


def rebuild_category(category, count):
    data = {
        "trees": (TREE_POINTS, create_tree),
        "houses": (HOUSE_POINTS, create_house),
        "clouds": (range(30), lambda index, point: create_cloud(index)),
        "sheep": (SHEEP_POINTS, create_sheep),
        "villagers": (VILLAGER_POINTS, create_villager),
        "monsters": (MONSTER_POINTS, create_monster),
    }

    points, creator = data[category]
    clear_group(GROUPS[category])

    for index, point in enumerate(list(points)[:count]):
        creator(index, point)


# Seasonal terrain, water, foliage, and snow all update together.
def _apply_season(value):
    palette = SEASONS[value]
    material("tree_foliage", palette["leaf"])
    material("island_deep_rock", palette["deep_rock"])
    material("island_blue_rock", palette["blue_rock"])
    material("island_violet_rock", palette["violet_rock"])
    material("island_lavender_rock", palette["lavender_rock"])

    if cmds.objExists(ROOT):
        create_environment()
        tree_count = cmds.intSliderGrp("treeSlider", query=True, value=True)
        house_count = cmds.intSliderGrp("houseSlider", query=True, value=True)
        rebuild_category("trees", tree_count)
        rebuild_category("houses", house_count)
        create_weather()
        update_time_of_day()


def apply_season(value, *_unused):
    with undo_chunk("Change island season"):
        _apply_season(value)


TIME_STOPS = (
    (0.0, "DEEP NIGHT", (.01, .02, .08), (.18, .25, .55), .16, .035, (.015, .035, .14)),
    (4.0, "MOONLIT NIGHT", (.025, .045, .13), (.30, .38, .72), .28, .075, (.025, .07, .20)),
    (4.9, "BLUE DAWN", (.12, .22, .42), (.48, .48, .75), .38, .09, (.04, .12, .30)),
    (5.7, "PEACH DAWN", (.48, .32, .49), (.96, .54, .46), .60, .13, (.08, .16, .36)),
    (6.5, "SUNRISE", (.86, .46, .31), (1.0, .50, .28), .82, .17, (.10, .20, .42)),
    (7.4, "ROSE MORNING", (.94, .62, .51), (1.0, .68, .44), 1.02, .21, (.08, .22, .48)),
    (9.0, "CLEAR MORNING", (.48, .72, .90), (1.0, .84, .64), 1.28, .28, (.04, .19, .48)),
    (11.0, "BRIGHT NOON", (.29, .62, .92), (1.0, .94, .77), 1.58, .36, (.03, .18, .52)),
    (12.5, "HIGH SUN", (.38, .70, .98), (1.0, .97, .84), 1.72, .39, (.035, .20, .56)),
    (14.0, "CRYSTAL AFTERNOON", (.31, .61, .90), (1.0, .86, .65), 1.46, .33, (.04, .18, .50)),
    (15.5, "AFTERNOON", (.38, .49, .67), (1.0, .70, .47), 1.12, .25, (.035, .14, .35)),
    (17.25, "GOLDEN HOUR", (.75, .43, .29), (1.0, .47, .22), .92, .20, (.09, .12, .29)),
    (18.75, "SUNSET", (.63, .23, .32), (1.0, .27, .16), .62, .14, (.12, .07, .25)),
    (20.25, "BLUE HOUR", (.08, .12, .30), (.38, .42, .75), .36, .09, (.035, .08, .20)),
    (21.5, "MOONLIT NIGHT", (.025, .045, .13), (.30, .38, .72), .28, .075, (.025, .07, .20)),
    (24.0, "DEEP NIGHT", (.01, .02, .08), (.18, .25, .55), .16, .035, (.015, .035, .14)),
)


def lerp(first, second, amount):
    return first + (second - first) * amount


def lerp_colour(first, second, amount):
    return tuple(lerp(a, b, amount) for a, b in zip(first, second))


def time_look(hour):
    """Interpolate lighting and colour continuously between named moments."""
    hour = max(0.0, min(24.0, float(hour)))

    for index in range(len(TIME_STOPS) - 1):
        start = TIME_STOPS[index]
        end = TIME_STOPS[index + 1]
        if hour <= end[0]:
            amount = (hour - start[0]) / (end[0] - start[0])
            label = start[1] if amount < .5 else end[1]
            return (
                label,
                lerp_colour(start[2], end[2], amount),
                lerp_colour(start[3], end[3], amount),
                lerp(start[4], end[4], amount),
                lerp(start[5], end[5], amount),
                lerp_colour(start[6], end[6], amount),
            )
    final = TIME_STOPS[-1]
    return final[1:]


def star_visibility(hour):
    """Fade stars in over dusk and out during dawn."""
    if 18.0 <= hour < 20.5:
        return (hour - 18.0) / 2.5
    if 4.0 < hour < 6.5:
        return 1.0 - ((hour - 4.0) / 2.5)
    if hour >= 20.5 or hour <= 4.0:
        return 1.0
    return 0.0


def apply_sky_gradient(sky, horizon):
    """Drive Maya's top/bottom viewport gradient, not one flat background."""
    top = lerp_colour(sky, (.015, .025, .08), .18)
    bottom = lerp_colour(sky, horizon, .66)
    try:
        cmds.displayPref(displayGradient=True)
        cmds.displayRGBColor("backgroundTop", top[0], top[1], top[2])
        cmds.displayRGBColor("backgroundBottom", bottom[0], bottom[1], bottom[2])
    except RuntimeError:
        # Batch Maya has no viewport preferences; interactive Maya does.
        pass
    cmds.displayRGBColor("background", bottom[0], bottom[1], bottom[2])


def enable_viewport_lighting():
    """Ensure the user sees this tool's lights instead of Maya default light."""
    for panel in cmds.getPanel(type="modelPanel") or []:
        try:
            cmds.modelEditor(panel, edit=True, displayLights="all")
            cmds.modelEditor(panel, edit=True, shadows=True)
        except RuntimeError:
            pass


def configure_sun_shadows(light):
    """Use shadows where this renderer supports them, without assuming a mode."""
    for attribute in ("useDepthMapShadows", "useRayTraceShadows"):
        if cmds.attributeQuery(attribute, node=light, exists=True):
            cmds.setAttr(light + "." + attribute, True)


def _apply_time_of_day():
    hour = cmds.floatSliderGrp("timeSlider", query=True, value=True)
    label, sky, light_colour, intensity, fill, water = time_look(hour)

    if cmds.control("timeReadout", exists=True):
        cmds.text(
            "timeReadout", edit=True,
            label="%s  ·  %04.1f:00" % (label, hour)
        )

    apply_sky_gradient(sky, light_colour)

    if not cmds.objExists(ROOT):
        return

    enable_viewport_lighting()
    daylight = max(0.0, math.sin((hour - 5.0) * math.pi / 15.0))
    if cmds.objExists("island_key_light"):
        cmds.setAttr(
            "island_key_light.intensity", .04 + daylight * intensity * 1.70
        )
        cmds.setAttr(
            "island_key_light.color",
            light_colour[0], light_colour[1], light_colour[2],
            type="double3"
        )
        light_transform = cmds.listRelatives(
            "island_key_light", parent=True, fullPath=True
        ) or []
        if light_transform:
            cmds.xform(
                light_transform[0],
                rotation=(-18 - daylight * 56, -108 + hour * 9, 0)
            )

    if cmds.objExists("island_fill_light"):
        cmds.setAttr("island_fill_light.intensity", .035 + daylight * (.10 + fill * .32))

    if cmds.objExists("island_sun_glow"):
        cmds.setAttr("island_sun_glow.intensity", .025 + daylight * .72)
        cmds.setAttr(
            "island_sun_glow.color",
            min(1.0, light_colour[0] * 1.06),
            min(1.0, light_colour[1] * .82),
            min(1.0, light_colour[2] * .58), type="double3"
        )
        glow_transform = cmds.listRelatives(
            "island_sun_glow", parent=True, fullPath=True
        ) or []
        if glow_transform:
            cmds.xform(
                glow_transform[0],
                rotation=(-12 - daylight * 42, 78 + hour * 8, 0)
            )

    if cmds.objExists("island_wall_bounce"):
        cmds.setAttr("island_wall_bounce.intensity", .02 + daylight * .48)
        cmds.setAttr(
            "island_wall_bounce.color",
            min(1.0, light_colour[0] * 1.05),
            min(1.0, light_colour[1] * .88),
            min(1.0, light_colour[2] * .72), type="double3"
        )
        bounce_transform = cmds.listRelatives(
            "island_wall_bounce", parent=True, fullPath=True
        ) or []
        if bounce_transform:
            cmds.xform(
                bounce_transform[0],
                rotation=(-32 - daylight * 26, 112 + hour * 8, 0)
            )

    if cmds.objExists("island_sky_fill"):
        cmds.setAttr("island_sky_fill.intensity", .10 + daylight * .20)
        cmds.setAttr("island_sky_fill.color", sky[0], sky[1], sky[2], type="double3")

    water_colour = bright_water(water)
    water_material("island_ocean", water_colour)
    water_material("island_water", water_colour)

    amount = star_visibility(hour)
    if cmds.objExists("island_stars_GRP"):
        cmds.setAttr("island_stars_GRP.visibility", amount > .01)
    if cmds.objExists("island_star_MAT"):
        transparency = 1.0 - amount
        cmds.setAttr(
            "island_star_MAT.transparency",
            transparency, transparency, transparency, type="double3"
        )
    if cmds.objExists("sky_moon"):
        moon_x = -(hour - 12.5) * 1.45 * island_width()
        moon_z = -16.0 * island_depth()
        cmds.xform(
            "sky_moon", worldSpace=True,
            translation=(moon_x, 5.0 + amount * 16.0, moon_z)
        )
        if cmds.objExists("island_moon_MAT"):
            moon_transparency = 1.0 - amount
            cmds.setAttr(
                "island_moon_MAT.transparency",
                moon_transparency, moon_transparency, moon_transparency,
                type="double3"
            )
    sun_x = (hour - 12.5) * 1.72 * island_width()
    sun_z = -17.0 * island_depth()
    if cmds.objExists("sky_sun"):
        cmds.xform(
            "sky_sun", worldSpace=True,
            translation=(sun_x, 4.0 + daylight * 18.0, sun_z)
        )
        cmds.setAttr("sky_sun.visibility", daylight > .01)
        glow_material("island_sun_disc", light_colour, .45)

    if cmds.objExists("island_sun_reflection_GRP"):
        cmds.setAttr("island_sun_reflection_GRP.visibility", daylight > .01)
        cmds.xform(
            "island_sun_reflection_GRP", worldSpace=True,
            translation=(sun_x * .38, 0, 0)
        )
        glow_material("ocean_sun_glitter", light_colour, .62)

    if cmds.objExists("island_moon_reflection_GRP"):
        cmds.setAttr("island_moon_reflection_GRP.visibility", amount > .01)
        cmds.xform(
            "island_moon_reflection_GRP", worldSpace=True,
            translation=(-sun_x * .30, 0, 0)
        )
        glow_material("ocean_moon_glitter", (.62, .77, 1.0), .34)


def update_time_of_day(*_unused):
    with undo_chunk("Change island time"):
        _apply_time_of_day()


def apply_time(*_unused):
    update_time_of_day()


def create_lights():
    clear_group(GROUPS["lights"])
    key = cmds.directionalLight(
        name="island_key_light",
        rotation=(-42, -28, 0)
    )
    fill = cmds.ambientLight(
        name="island_fill_light",
        intensity=.12
    )
    glow = cmds.directionalLight(
        name="island_sun_glow",
        rotation=(-30, 120, 0), intensity=.35
    )
    sky_fill = cmds.directionalLight(
        name="island_sky_fill",
        rotation=(-55, -35, 0), intensity=.16
    )
    wall_bounce = cmds.directionalLight(
        name="island_wall_bounce",
        rotation=(-42, 110, 0), intensity=.22
    )

    configure_sun_shadows(key)
    for light in (key, fill, glow, sky_fill, wall_bounce):
        transform = cmds.listRelatives(
            light, parent=True, fullPath=True
        ) or [light]
        cmds.parent(transform[0], GROUPS["lights"])


# Internal build: it only removes the known root group and makes a new one.
def _build_island():
    if cmds.objExists(ROOT):
        cmds.delete(ROOT)

    root = cmds.group(empty=True, name=ROOT)

    for name in GROUPS.values():
        ensure_group(name, root)

    create_environment()
    create_lights()

    for category, (control, _maximum) in POPULATION_CONTROLS.items():
        rebuild_category(
            category,
            cmds.intSliderGrp(control, query=True, value=True)
        )

    create_weather()
    _apply_time_of_day()
    cmds.select(ROOT)


def build_island(*_unused):
    with undo_chunk("Build fantasy island"):
        _build_island()


def update_slider(category, control, *_unused):
    if cmds.objExists(ROOT):
        with undo_chunk("Update island population"):
            rebuild_category(
                category, cmds.intSliderGrp(control, query=True, value=True)
            )


def delete_island(*_unused):
    with undo_chunk("Delete fantasy island"):
        if cmds.objExists(ROOT):
            cmds.delete(ROOT)


def island_width():
    if cmds.control("islandWidthSlider", exists=True):
        return cmds.floatSliderGrp(
            "islandWidthSlider", query=True, value=True
        )
    return 1.0


def island_depth():
    if cmds.control("islandDepthSlider", exists=True):
        return cmds.floatSliderGrp(
            "islandDepthSlider", query=True, value=True
        )
    return 1.0


def apply_island_scale():
    """The root stays at 1.0; the generator creates real wide/deep geometry."""
    if cmds.objExists(ROOT):
        cmds.setAttr(ROOT + ".scaleX", 1.0)
        cmds.setAttr(ROOT + ".scaleY", 1.0)
        cmds.setAttr(ROOT + ".scaleZ", 1.0)


def update_island_scale(*_unused):
    if cmds.objExists(ROOT):
        with undo_chunk("Resize and ground fantasy island"):
            _build_island()


def update_world_seed(*_unused):
    if cmds.objExists(ROOT):
        with undo_chunk("Regenerate organic island"):
            _build_island()


def rebuild_environment_controls(*_unused):
    if cmds.objExists(ROOT):
        with undo_chunk("Update land and water"):
            create_environment()
            _apply_time_of_day()


def current_blueprint():
    return {
        "format": PRESET_FORMAT,
        "version": PRESET_VERSION,
        "land": {
            "width": island_width(),
            "depth": island_depth(),
            "detail": cmds.intSliderGrp("detailSlider", query=True, value=True),
            "seed": world_seed(),
            "water_feature": water_feature(),
            "water_size": water_size(),
        },
        "life": {
            category: cmds.intSliderGrp(control, query=True, value=True)
            for category, (control, _maximum) in POPULATION_CONTROLS.items()
        },
        "atmosphere": {
            "season": season(),
            "weather": weather(),
            "time": cmds.floatSliderGrp("timeSlider", query=True, value=True),
        },
    }


def validate_blueprint(data):
    if not isinstance(data, dict) or data.get("format") != PRESET_FORMAT:
        raise ValueError("This is not a Fantasy Island Simulator blueprint.")
    if data.get("version") != PRESET_VERSION:
        raise ValueError("This blueprint uses an unsupported version.")

    land = data.get("land")
    life = data.get("life")
    atmosphere = data.get("atmosphere")
    if not all(isinstance(item, dict) for item in (land, life, atmosphere)):
        raise ValueError("The blueprint is missing a required section.")

    width, depth, water_size_value = (
        land.get("width"), land.get("depth"), land.get("water_size")
    )
    for label, value, low, high in (
        ("width", width, 1.0, 2.5),
        ("depth", depth, 1.0, 2.2),
        ("water size", water_size_value, .5, 2.0),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("%s must be a number." % label)
        if not low <= value <= high:
            raise ValueError("%s must be between %s and %s." % (label, low, high))

    detail = land.get("detail")
    if detail not in (1, 2, 3):
        raise ValueError("detail must be 1, 2, or 3.")
    seed = land.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed <= 999:
        raise ValueError("seed must be a whole number from 1 to 999.")
    if land.get("water_feature") not in ("None", "Lake", "River"):
        raise ValueError("The blueprint has an unknown water feature.")

    safe_life = {}
    for category, (_control, maximum) in POPULATION_CONTROLS.items():
        value = life.get(category)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("%s must be a whole number." % category)
        if not 0 <= value <= maximum:
            raise ValueError("%s is outside its slider range." % category)
        safe_life[category] = value

    if atmosphere.get("season") not in SEASONS:
        raise ValueError("The blueprint has an unknown season.")
    # Version-1 blueprints saved before weather existed remain usable: their
    # intentional default is Clear. New files always write the weather field.
    saved_weather = atmosphere.get("weather", "Clear")
    if saved_weather not in ("Clear", "Rain", "Snow"):
        raise ValueError("The blueprint has an unknown weather setting.")
    saved_time = atmosphere.get("time")
    if isinstance(saved_time, bool) or not isinstance(saved_time, (int, float)):
        raise ValueError("time must be a number from 0 to 24.")
    if not 0.0 <= saved_time <= 24.0:
        raise ValueError("time must be from 0 to 24.")

    return {
        "land": {
            "width": float(width), "depth": float(depth),
            "detail": detail, "seed": seed,
            "water_feature": land["water_feature"],
            "water_size": float(water_size_value),
        },
        "life": safe_life,
        "atmosphere": {
            "season": atmosphere["season"], "weather": saved_weather,
            "time": float(atmosphere["time"]),
        },
    }


def save_blueprint(*_unused):
    paths = cmds.fileDialog2(
        caption="Save Island Blueprint",
        fileMode=0,
        fileFilter="Fantasy Island Blueprint (*.json)",
        dialogStyle=2,
    )
    if not paths:
        return

    path = paths[0]
    if not path.lower().endswith(".json"):
        path += ".json"

    try:
        with open(path, "w") as blueprint_file:
            json.dump(current_blueprint(), blueprint_file, indent=2, sort_keys=True)
    except (OSError, TypeError, ValueError) as error:
        cmds.confirmDialog(
            title="Blueprint not saved",
            message="Could not save this blueprint:\n%s" % error,
            button=["OK"], icon="critical",
        )
        return

    cmds.confirmDialog(
        title="Blueprint saved",
        message="Saved a reusable island blueprint:\n%s" % path,
        button=["OK"], icon="information",
    )


def load_blueprint(*_unused):
    paths = cmds.fileDialog2(
        caption="Load Island Blueprint",
        fileMode=1,
        fileFilter="Fantasy Island Blueprint (*.json)",
        dialogStyle=2,
    )
    if not paths:
        return

    try:
        with open(paths[0], "r") as blueprint_file:
            blueprint = validate_blueprint(json.load(blueprint_file))
    except (OSError, TypeError, ValueError) as error:
        cmds.confirmDialog(
            title="Blueprint not loaded",
            message="Your scene was left unchanged.\n%s" % error,
            button=["OK"], icon="critical",
        )
        return

    with undo_chunk("Load island blueprint"):
        cmds.floatSliderGrp(
            "islandWidthSlider", edit=True, value=blueprint["land"]["width"]
        )
        cmds.floatSliderGrp(
            "islandDepthSlider", edit=True, value=blueprint["land"]["depth"]
        )
        cmds.intSliderGrp(
            "detailSlider", edit=True, value=blueprint["land"]["detail"]
        )
        cmds.intSliderGrp(
            "worldSeedSlider", edit=True, value=blueprint["land"]["seed"]
        )
        set_water_feature(blueprint["land"]["water_feature"], rebuild=False)
        cmds.floatSliderGrp(
            "waterSizeSlider", edit=True,
            value=blueprint["land"]["water_size"]
        )
        for category, (control, _maximum) in POPULATION_CONTROLS.items():
            cmds.intSliderGrp(
                control, edit=True, value=blueprint["life"][category]
            )
        set_season(blueprint["atmosphere"]["season"], rebuild=False)
        set_weather(blueprint["atmosphere"]["weather"], rebuild=False)
        cmds.floatSliderGrp(
            "timeSlider", edit=True, value=blueprint["atmosphere"]["time"]
        )
        _build_island()

    cmds.confirmDialog(
        title="Blueprint loaded",
        message="Loaded the blueprint and rebuilt only Fantasy Island.",
        button=["OK"], icon="information",
    )


def ui_section(icon, title, subtitle, colour):
    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=2,
        columnWidth2=(38, 280),
        columnAttach2=("both", "both")
    )
    cmds.text(
        label=icon, align="center", font="boldLabelFont", height=28,
        backgroundColor=colour
    )
    cmds.text(
        label="  " + title, align="left", font="obliqueLabelFont", height=28,
        backgroundColor=colour
    )
    cmds.setParent("..")
    cmds.text(
        label=subtitle, align="left", font="smallPlainLabelFont", height=20
    )
    cmds.separator(style="in", height=7)


def show_ui():
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)

    cmds.window(
        WINDOW,
        title="Fantasy Island Simulator | Maya 2026",
        sizeable=True, widthHeight=(370, 720),
        backgroundColor=UI["window"]
    )
    # The controls are intentionally rich now, so the interface scrolls
    # instead of stretching beyond a laptop screen.
    cmds.scrollLayout(
        "fantasyIslandScroll", childResizable=True,
        verticalScrollBarThickness=16
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=7)

    cmds.text(
        label="✿  little island studio  ✿",
        align="center", font="obliqueLabelFont", height=38,
        backgroundColor=UI["header"]
    )
    cmds.text(
        label="make a small world, softly · seasons · stories · sunlight",
        align="center", font="smallObliqueLabelFont", height=24,
        backgroundColor=UI["subheader"]
    )

    ui_section(
        "⛰", "LAND & WATER",
        "Stretch the world, then choose how water shapes it.", UI["land"]
    )
    cmds.floatSliderGrp(
        "islandWidthSlider", label="⟷  Island Width", field=True,
        minValue=1.0, maxValue=2.5, value=1.65,
        columnWidth3=(115, 45, 175),
        dragCommand=update_island_scale,
        changeCommand=update_island_scale
    )
    cmds.floatSliderGrp(
        "islandDepthSlider", label="↕  Island Depth", field=True,
        minValue=1.0, maxValue=2.2, value=1.35,
        columnWidth3=(115, 45, 175),
        dragCommand=update_island_scale,
        changeCommand=update_island_scale
    )
    cmds.intSliderGrp(
        "detailSlider", label="◇  Ground Detail", field=True,
        minValue=1, maxValue=3, value=2,
        columnWidth3=(115, 45, 175),
        changeCommand=rebuild_environment_controls
    )
    cmds.intSliderGrp(
        "worldSeedSlider", label="✦  World Seed", field=True,
        minValue=1, maxValue=999, value=184,
        columnWidth3=(115, 45, 175),
        changeCommand=update_world_seed
    )
    cmds.text(
        label="≈  Choose Water", align="left",
        font="smallBoldLabelFont", height=20
    )
    cmds.rowLayout(
        numberOfColumns=3, adjustableColumn=3,
        columnWidth3=(110, 110, 110)
    )
    for label, value, colour in (
        ("◇  NONE", "None", (.29, .31, .38)),
        ("◯  LAKE", "Lake", (.24, .44, .62)),
        ("≈  RIVER", "River", (.20, .36, .56)),
    ):
        cmds.iconTextButton(
            style="textOnly", label=label, height=30,
            command=lambda *_unused, selected=value: set_water_feature(selected),
            backgroundColor=colour
        )
    cmds.setParent("..")
    cmds.text(
        "waterReadout", label="WATER FEATURE  ·  LAKE",
        align="center", font="smallBoldLabelFont", height=22,
        backgroundColor=(.19, .22, .33)
    )
    cmds.floatSliderGrp(
        "waterSizeSlider", label="≈  Water Size", field=True,
        minValue=.5, maxValue=2.0, value=1.0,
        columnWidth3=(115, 45, 175),
        dragCommand=rebuild_environment_controls,
        changeCommand=rebuild_environment_controls
    )

    ui_section(
        "♣", "ISLAND LIFE",
        "Choose the creatures and people who make the island feel alive.",
        UI["life"]
    )
    controls = (
        ("treeSlider", "♣  Trees", "trees", 30, 16),
        ("houseSlider", "⌂  Houses", "houses", 10, 5),
        ("cloudSlider", "☁  Clouds", "clouds", 30, 10),
        ("sheepSlider", "●  Sheep Flocks", "sheep", 15, 5),
        ("villagerSlider", "♟  Villager Groups", "villagers", 10, 4),
        ("monsterSlider", "◆  Monsters", "monsters", 8, 2),
    )
    for control, label, category, maximum, default in controls:
        cmds.intSliderGrp(
            control, label=label, field=True, minValue=0,
            maxValue=maximum, value=default,
            columnWidth3=(115, 45, 175),
            changeCommand=lambda unused, c=category, ui=control:
                update_slider(c, ui)
        )

    ui_section(
        "☀", "ATMOSPHERE",
        "Move the sun with your hand and transform the whole island.",
        UI["atmosphere"]
    )
    cmds.text(
        label="❄  Choose a Season", align="left",
        font="smallBoldLabelFont", height=20
    )
    cmds.rowLayout(
        numberOfColumns=4, adjustableColumn=4,
        columnWidth4=(82, 82, 82, 82)
    )
    for label, value, colour in (
        ("✿ SPRING", "Spring", (.32, .47, .38)),
        ("☀ SUMMER", "Summer", (.45, .40, .20)),
        ("❋ AUTUMN", "Autumn", (.49, .25, .15)),
        ("❄ WINTER", "Winter", (.30, .38, .55)),
    ):
        cmds.iconTextButton(
            style="textOnly", label=label, height=32,
            command=lambda *_unused, selected=value: set_season(selected),
            backgroundColor=colour
        )
    cmds.setParent("..")
    cmds.text(
        "seasonReadout", label="CURRENT SEASON  ·  SPRING",
        align="center", font="smallBoldLabelFont", height=22,
        backgroundColor=(.19, .22, .33)
    )
    cmds.text(
        label="☁  Choose the Weather", align="left",
        font="smallBoldLabelFont", height=20
    )
    cmds.rowLayout(
        numberOfColumns=3, adjustableColumn=3,
        columnWidth3=(110, 110, 110)
    )
    for label, value, colour in (
        ("☀  CLEAR", "Clear", (.30, .43, .50)),
        ("☂  RAIN", "Rain", (.23, .36, .58)),
        ("❄  SNOW", "Snow", (.50, .58, .68)),
    ):
        cmds.iconTextButton(
            style="textOnly", label=label, height=30,
            command=lambda *_unused, selected=value: set_weather(selected),
            backgroundColor=colour
        )
    cmds.setParent("..")
    cmds.text(
        "weatherReadout", label="CURRENT WEATHER  ·  CLEAR",
        align="center", font="smallBoldLabelFont", height=22,
        backgroundColor=(.19, .22, .33)
    )
    cmds.floatSliderGrp(
        "timeSlider", label="☀  Time of Day", field=True,
        minValue=0.0, maxValue=24.0, value=14.0, step=.25,
        columnWidth3=(115, 45, 175),
        dragCommand=update_time_of_day,
        changeCommand=update_time_of_day,
        backgroundColor=(.47, .28, .16)
    )
    cmds.text(
        "timeReadout", label="DAYTIME  ·  14:00", align="center",
        font="smallBoldLabelFont", height=24,
        backgroundColor=(.19, .22, .33)
    )

    ui_section(
        "✦", "BUILD YOUR WORLD",
        "Save a blueprint, build the island, or remove only your creation.",
        UI["action"]
    )
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnWidth2=(165, 165))
    cmds.iconTextButton(
        style="textOnly", label="↧  SAVE BLUEPRINT", height=31,
        font="boldLabelFont", command=save_blueprint,
        backgroundColor=UI["save"]
    )
    cmds.iconTextButton(
        style="textOnly", label="↥  LOAD BLUEPRINT", height=31,
        font="boldLabelFont", command=load_blueprint,
        backgroundColor=(.31, .30, .50)
    )
    cmds.setParent("..")
    cmds.iconTextButton(
        style="textOnly", label="✦  CREATE / REBUILD ISLAND  ✦",
        height=42, font="boldLabelFont", command=build_island,
        backgroundColor=UI["build"]
    )
    cmds.iconTextButton(
        style="textOnly", label="✕  DELETE ONLY MY ISLAND",
        height=32, command=delete_island, backgroundColor=UI["delete"]
    )
    cmds.text(
        label="Everything generated stays inside fantasyIsland_GRP.",
        align="center", font="smallObliqueLabelFont", height=24
    )

    cmds.showWindow(WINDOW)
    _apply_time_of_day()


show_ui()
