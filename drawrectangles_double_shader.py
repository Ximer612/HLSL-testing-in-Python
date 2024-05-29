import glfw
from compushady import Texture2D, Swapchain, Compute, Buffer, HEAP_UPLOAD, HEAP_DEFAULT, HEAP_READBACK
from compushady.formats import B8G8R8A8_UNORM, R32_UINT
from compushady.shaders import hlsl
import struct

import compushady.config
compushady.config.set_debug(True)

rectangles = []

stats_buffer = Buffer(4 *4 , HEAP_DEFAULT, format=R32_UINT)
stats_buffer_readback = Buffer(stats_buffer.size, HEAP_READBACK)

def add_rectangle_buffer(r,g,b,x,y,w,h):
    rectangles.append((r,g,b, x,y, w,h))
    pass

def upload_rectangles(rectangles):
    rectangle_variables = 3+2+2 #rgb 3 xy 2 wh 2

    rectangle_buffer = Buffer(len(rectangles) * (rectangle_variables) * 4, HEAP_UPLOAD)

    for index, rectangle in enumerate(rectangles):
        rectangle_buffer.upload(struct.pack("<7f",rectangle[0],rectangle[1],rectangle[2],rectangle[3],rectangle[4],rectangle[5],rectangle[6]), (index) * rectangle_variables * 4)
    
    fast_buffer = Buffer(rectangle_buffer.size, HEAP_DEFAULT, stride=len(rectangles))
    rectangle_buffer.copy_to(fast_buffer)

    return fast_buffer

def upload_config(rectangles,background_color:tuple[3]):
    config_buffer = Buffer( (1 + 3) * 4, HEAP_UPLOAD)
    config_buffer.upload(struct.pack("<Ifff",len(rectangles),background_color[0],background_color[1],background_color[2]))

    fast_buffer = Buffer(config_buffer.size, HEAP_DEFAULT, stride=1)
    config_buffer.copy_to(fast_buffer)

    return fast_buffer

add_rectangle_buffer(1,0,0,     0,0,        100,100)
add_rectangle_buffer(0,1,0,     200,0,      100,100)
add_rectangle_buffer(0,0,1,     0,200,      100,100)
add_rectangle_buffer(1,0,1,     200,200,    100,100)

fast_rectangles_buffer = upload_rectangles(rectangles)

with open("shaders/rectangles_structured_double_shader.hlsl", "r") as file:
    shader_file = file.read()

shader = hlsl.compile(shader_file)

with open("shaders/clear_screen.hlsl", "r") as file:
    clear_shader_file = file.read()

shader_clear = hlsl.compile(clear_shader_file)

movement_buffer = Buffer(2*4 + 2*4,HEAP_UPLOAD)

fast_config_buffer = upload_config(rectangles,(0.5,0.5,0.5))

glfw.init()
#disable default opengl gpu access
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
target = Texture2D(512,512, B8G8R8A8_UNORM)

compute_clear = Compute(shader_clear, uav=[target,stats_buffer], srv=[fast_config_buffer])
compute = Compute(shader, uav=[target,stats_buffer], srv=[fast_rectangles_buffer,fast_config_buffer], cbv=[movement_buffer])

window = glfw.create_window(target.width,target.height, "Double shader", None, None)
swapchain = Swapchain(glfw.get_win32_window(window), B8G8R8A8_UNORM,2)

pos_x,pos_y = 100,100
camera_x,camera_y = 0,0

readback_buffer = Buffer(fast_rectangles_buffer.size, HEAP_READBACK)
fast_rectangles_buffer.copy_to(readback_buffer)

def key_event(window,key,scancode,action,mods):
    global camera_x
    global camera_y

    speed = 10

    if key == glfw.KEY_W and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_y -= speed
    if key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_y += speed
    if key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_x -= speed
    if key == glfw.KEY_D and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_x += speed

glfw.set_key_callback(window,key_event)

while not glfw.window_should_close(window):
    glfw.poll_events()

    movement_buffer.upload(struct.pack("<ffff",pos_x,pos_y,camera_x,camera_y))

    compute_clear.dispatch(target.width //8, target.height // 8, 1)
    compute.dispatch(target.width //8, target.height // 8, 1)
    swapchain.present(target)

    stats_buffer.copy_to(stats_buffer_readback)
    print(struct.unpack("<I",stats_buffer_readback.readback(4)))