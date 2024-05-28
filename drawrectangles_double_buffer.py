from math import cos, sin
import glfw
from compushady import Texture2D, Swapchain, Compute, Buffer, HEAP_UPLOAD, HEAP_DEFAULT
from compushady.formats import B8G8R8A8_UNORM
from compushady.shaders import hlsl
from compushady.formats import R32G32B32A32_FLOAT, R32G32B32_FLOAT
import struct

import compushady.config
compushady.config.set_debug(True)

rectangles = []
rectangles_colors = []

def add_rectangle_buffer(r,g,b,x,y,w,h):
    rectangles_colors.append((r,g,b))
    rectangles.append((x,y,w,h))
    pass
    
def upload_rectangles(rectangles, colorR, colorG, colorB):

    rectangle_buffer = Buffer(len(rectangles) * 4 * 4 + 4 * 4, HEAP_UPLOAD)
    rectangle_buffer.upload(struct.pack("<Ifff",len(rectangles),colorR,colorG,colorB))
    for index, rectangle in enumerate(rectangles):
        rectangle_buffer.upload(struct.pack("<ffff",rectangle[0],rectangle[1],rectangle[2],rectangle[3]), index * 4 * 4 + 4 * 4)
    
    fast_buffer = Buffer(len(rectangles)*4*4 + 4*4, HEAP_DEFAULT, format=R32G32B32A32_FLOAT)
    rectangle_buffer.copy_to(fast_buffer)

    return fast_buffer

def upload_colors():
    colors_buffer = Buffer(len(rectangles_colors) * 3 * 4, HEAP_UPLOAD)

    for index, color in enumerate(rectangles_colors):
        colors_buffer.upload(struct.pack("<fff",color[0],color[1],color[2]), index * 3 * 4)
    
    fast_buffer = Buffer(len(rectangles_colors) * 3 * 4 , HEAP_DEFAULT, format=R32G32B32_FLOAT)
    colors_buffer.copy_to(fast_buffer)

    return fast_buffer
    

add_rectangle_buffer(1,0,0, 0,0,    240,240)
add_rectangle_buffer(0,1,0, 250,0,  240,240)
add_rectangle_buffer(0,0,1, 0,250,  240,240)
add_rectangle_buffer(1,0,1, 250,250,240,240)

rectangles_fast_buffer = upload_rectangles(rectangles,0.5,0.5,0.5)
colors_fast_buffer = upload_colors()

with open("shaders/rectangles_double_buffer.hlsl", "r") as file:
    shader_file = file.read()

shader = hlsl.compile(shader_file)

configBuffer = Buffer(2*4,HEAP_UPLOAD)

glfw.init()
#disable default opengl gpu access
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)

target = Texture2D(512,512, B8G8R8A8_UNORM)
compute = Compute(shader, uav=[target], srv=[rectangles_fast_buffer,colors_fast_buffer], cbv=[configBuffer])

window = glfw.create_window(target.width,target.height, "Double buffer rectangles", None, None)

swapchain = Swapchain(glfw.get_win32_window(window), B8G8R8A8_UNORM,2)

x,y = 0,0

time = 0

while not glfw.window_should_close(window):
    glfw.poll_events()
    time = glfw.get_time()

    x = cos(time * 5) * 10
    y = sin(time * 5) * 10

    configBuffer.upload(struct.pack("<ff",x,y))

    compute.dispatch(target.width //8, target.height // 8, 1)
    swapchain.present(target)
