import glfw
from compushady import Texture2D, Swapchain, Compute, Buffer, HEAP_UPLOAD, HEAP_DEFAULT, HEAP_READBACK
from compushady.formats import B8G8R8A8_UNORM
from compushady.shaders import hlsl
from compushady.formats import R32G32B32A32_FLOAT, R32_UINT, R32G32B32_FLOAT, R32G32B32_UINT
import struct

import compushady.config
import numpy
import math
import trimesh
import random

compushady.config.set_debug(True)

def identity_matrix():
    return numpy.array((
        (1, 0, 0, 0),
        (0, 1, 0, 0),
        (0, 0, 1, 0),
        (0, 0, 0, 1),
    ), dtype=numpy.float32)

def translation_matrix(x, y, z):
    return numpy.array(
        (
            (1, 0, 0, x),
            (0, 1, 0, y),
            (0, 0, 1, z),
            (0, 0, 0, 1),
        ),
        dtype=numpy.float32,
    )

def rotation_matrix_y(angle):
    return numpy.array((
        (numpy.cos(angle),  0, numpy.sin(angle),  0),
        (0,                 1,                0,  0),
        (-numpy.sin(angle), 0, numpy.cos(angle),  0),
        (0,                 0,                0,  1),
    ), dtype=numpy.float32
    )

def perspective_matrix(left, right, top, bottom, near, far):
    return numpy.array((
        ((2 * near) / (right - left), 0, 0, (right+left) / (right-left)),
        (0, (2 * near) / (top-bottom), 0, (top+bottom)/(top-bottom)),
        (0, 0, -(far + near) / (far-near), -(2 * far * near)/(far-near)),
        (0, 0, -1, 0)
    ), dtype=numpy.float32
    )

def perspective_matrix_fov(fov, aspect_ratio, near, far):
    top = near * numpy.tan(fov / 2)
    bottom = -top
    right = top * aspect_ratio
    left = -right
    return perspective_matrix(left, right, top, bottom, near, far)

def new_buffer(nparray, format):
    data = nparray.tobytes()
    upload = Buffer(len(data), HEAP_UPLOAD)
    upload.upload(data)
    in_gpu = Buffer(len(data), format=format)
    upload.copy_to(in_gpu)
    return in_gpu

def read_shader(file_path):
    with open(file_path, "r") as file:
        shader_file = file.read()

    return hlsl.compile(shader_file)

mesh = trimesh.creation.box((2, 2, 2))

stats_buffer = Buffer(64, HEAP_DEFAULT, format = R32_UINT)
stats_buffer_readback = Buffer(stats_buffer.size, HEAP_READBACK)

vertex_buffer = new_buffer(mesh.vertices.astype(numpy.float32), format=R32G32B32_FLOAT)
index_buffer = new_buffer(mesh.faces.astype(numpy.uint32), format=R32G32B32_UINT)

colors = []
for face in mesh.faces:
    colors.append([random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)])

color_buffer = new_buffer(numpy.array(colors, numpy.float32), format=R32G32B32_FLOAT)

configBuffer = Buffer(256, HEAP_UPLOAD)

perspective = perspective_matrix_fov(math.radians(90), 1, 0.01, 100)

shader = read_shader("shaders/mesh_rasterization.hlsl")
clear_shader = read_shader("shaders/simple_clear_screen.hlsl")

glfw.init()
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)

target = Texture2D(512,512, B8G8R8A8_UNORM)
compute = Compute(shader, uav=[target, stats_buffer], srv=[vertex_buffer, index_buffer, color_buffer], cbv=[configBuffer])
clear_compute = Compute(clear_shader, uav=[target, stats_buffer])

window = glfw.create_window(target.width,target.height, "Hello", None, None) 

swapchain = Swapchain(glfw.get_win32_window(window), B8G8R8A8_UNORM,2)

x,y = 0,0
camera_x, camera_y, camera_z = 0,-2,-5


def key_event(window,key,scancode,action,mods):
    global camera_x
    global camera_y
    global camera_z

    speed = 0.1

    if key == glfw.KEY_W and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_y += speed
    if key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_y -= speed
    if key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_x -= speed
    if key == glfw.KEY_D and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_x += speed
    if key == glfw.KEY_Q and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_z -= speed
    if key == glfw.KEY_E and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_z += speed

r = 0
glfw.set_key_callback(window,key_event)
while not glfw.window_should_close(window):
    glfw.poll_events()

    x+=1
    y+=1
    r += 0.01
    configBuffer.upload(perspective.tobytes() + translation_matrix(camera_x, camera_y, camera_z).tobytes() + rotation_matrix_y(r).tobytes() + struct.pack("<ffI", x , y, len(mesh.faces)))
    
    clear_compute.dispatch(target.width // 8, target.height // 8, 1)
    compute.dispatch(target.width //8, target.height // 8, 1)
    swapchain.present(target)
    stats_buffer.copy_to(stats_buffer_readback)
    print(struct.unpack("<I", stats_buffer_readback.readback(4)))