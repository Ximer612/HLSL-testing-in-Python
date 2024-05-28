import glfw
from compushady import Texture2D, Swapchain, Compute, Buffer, HEAP_UPLOAD, HEAP_DEFAULT, HEAP_READBACK
from compushady.formats import B8G8R8A8_UNORM
from compushady.shaders import hlsl
from compushady.formats import R32G32B32A32_FLOAT
import struct

import compushady.config
compushady.config.set_debug(True)

rectangles = []

def add_rectangle_buffer(r,g,b,x,y,w,h):
    rectangles.append((r,g,b, x,y, w,h))
    pass

def upload_rectangles(rectangles):
    # length of rectangles * single rectangle variables number * 4 bytes + background color variables length * 4 bytes

    rectangle_variables = 7 #rgb 3 xy 2 wh 2

    rectangle_buffer = Buffer(len(rectangles) * (rectangle_variables) * 4, HEAP_UPLOAD)

    for index, rectangle in enumerate(rectangles):
        rectangle_buffer.upload(struct.pack("<fffffff",rectangle[0],rectangle[1],rectangle[2],rectangle[3],rectangle[4],rectangle[5],rectangle[6]), (index) * rectangle_variables * 4)
    
    fast_buffer = Buffer(rectangle_buffer.size, HEAP_DEFAULT, format=R32G32B32A32_FLOAT)
    rectangle_buffer.copy_to(fast_buffer)

    return fast_buffer

def upload_config(rectangles,background_color:tuple[3]):
    config_buffer = Buffer( (1 + 3) * 4, HEAP_UPLOAD)
    config_buffer.upload(struct.pack("<Ifff",len(rectangles),background_color[0],background_color[1],background_color[2]))

    fast_buffer = Buffer(config_buffer.size, HEAP_DEFAULT, format=R32G32B32A32_FLOAT)
    config_buffer.copy_to(fast_buffer)

    return fast_buffer

add_rectangle_buffer(1,0,0, 0,0,    240,240)
add_rectangle_buffer(0,1,0, 250,0,  240,240)
add_rectangle_buffer(0,0,1, 0,250,  240,240)
add_rectangle_buffer(1,0,1, 250,250,240,240)

fast_rectangles_buffer = upload_rectangles(rectangles)

with open("shaders/rectangles_structured.hlsl", "r") as file:
    shader_file = file.read()

shader = hlsl.compile(shader_file)

movement_buffer = Buffer(2*4,HEAP_UPLOAD)

fast_config_buffer = upload_config(rectangles,(0.5,0.5,0.5))

glfw.init()
#disable default opengl gpu access
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
target = Texture2D(512,512, B8G8R8A8_UNORM)

compute = Compute(shader, uav=[target], srv=[fast_rectangles_buffer,fast_config_buffer], cbv=[movement_buffer])

window = glfw.create_window(target.width,target.height, "Structured draw rectangles", None, None)
swapchain = Swapchain(glfw.get_win32_window(window), B8G8R8A8_UNORM,2)

pos_x,pos_y = 0,0

readback_buffer = Buffer(fast_config_buffer.size, HEAP_READBACK)
fast_config_buffer.copy_to(readback_buffer)
print("Config Buffer = " + str(struct.unpack("<1I3f",readback_buffer.readback(4*4))))

readback_buffer = Buffer(fast_rectangles_buffer.size, HEAP_READBACK)
fast_rectangles_buffer.copy_to(readback_buffer)

for index in range(0,len(rectangles)):
    print(str(index) + "° Rectangle Buffer = " + str(struct.unpack("<7f",readback_buffer.readback(7*4,7*4*index))))

def key_event(window,key,scancode,action,mods):
    global pos_x
    global pos_y

    speed = 25

    if action == glfw.PRESS and key == glfw.KEY_W:
        pos_y -= speed
    if action == glfw.PRESS and key == glfw.KEY_S:
        pos_y += speed
    if action == glfw.PRESS and key == glfw.KEY_A:
        pos_x -= speed
    if action == glfw.PRESS and key == glfw.KEY_D:
        pos_x += speed

while not glfw.window_should_close(window):
    glfw.poll_events()

    glfw.set_key_callback(window,key_event)

    movement_buffer.upload(struct.pack("<ff",pos_x,pos_y))

    compute.dispatch(target.width //8, target.height // 8, 1)
    swapchain.present(target)