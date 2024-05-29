import glfw
from compushady import Texture2D, Swapchain, Compute, Buffer, HEAP_UPLOAD, HEAP_DEFAULT, HEAP_READBACK
from compushady.formats import B8G8R8A8_UNORM, R32_UINT, R32G32B32_FLOAT
from compushady.shaders import hlsl
import struct

import compushady.config
compushady.config.set_debug(True)

triangles = []

stats_buffer = Buffer(64 * 4, HEAP_DEFAULT, format=R32_UINT)
stats_buffer_readback = Buffer(stats_buffer.size, HEAP_READBACK)

def add_triangle_buffer(triangle1,triangle2,triangle3,color):
    triangles.append((triangle1[0],triangle1[1],triangle1[2], triangle2[0],triangle2[1],triangle2[2],triangle3[0],triangle3[1],triangle3[2],color[0],color[1],color[2]))
    pass

def upload_triangles(triangles):
    triangles_variables_size = 3 * 4 # 3 triangles and 1 color

    triangles_buffer = Buffer(len(triangles) * (triangles_variables_size) * 4, HEAP_UPLOAD)

    for index, triangle in enumerate(triangles):
        triangles_buffer.upload(struct.pack("<12f", triangle[0],triangle[1],triangle[2],
                                                    triangle[3],triangle[4],triangle[5],
                                                    triangle[6],triangle[7],triangle[8],
                                                    triangle[9],triangle[10],triangle[11]),
                                            (index) * triangles_variables_size * 4)
    
    fast_buffer = Buffer(triangles_buffer.size, HEAP_DEFAULT, format=R32G32B32_FLOAT)
    triangles_buffer.copy_to(fast_buffer)

    return fast_buffer

add_triangle_buffer([0,1,0],[-1,-1,0],[1,1,0],[0,1,0])
add_triangle_buffer([0, 0.8, 0], [-0.8, -0.8, 0], [0.8, -0.8, 0], [1, 0, 0])
add_triangle_buffer([0, 0.4, 0], [-0.4, -0.4, 0], [0.4, -0.4, 0], [0, 0, 1])

fast_rectangles_buffer = upload_triangles(triangles)

def read_shader(file_path):
    with open(file_path, "r") as file:
        shader_file = file.read()

    return hlsl.compile(shader_file)

shader_clear = read_shader("shaders/simple_clear_screen.hlsl")

shader = read_shader("shaders/triangle_rasterization.hlsl")

configBuffer = Buffer(24, HEAP_UPLOAD)

glfw.init()
#disable default opengl gpu access
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)

target = Texture2D(512,512, B8G8R8A8_UNORM)
compute_clear = Compute(shader_clear, uav=[target,stats_buffer], srv=[fast_rectangles_buffer])
compute = Compute(shader, uav=[target,stats_buffer], srv=[fast_rectangles_buffer], cbv=[configBuffer])

window = glfw.create_window(target.width,target.height, "Draw triangles", None, None)
swapchain = Swapchain(glfw.get_win32_window(window), B8G8R8A8_UNORM,2)

pos_x,pos_y = 0,0
camera_x,camera_y = 0,0

readback_buffer = Buffer(fast_rectangles_buffer.size, HEAP_READBACK)
fast_rectangles_buffer.copy_to(readback_buffer)

def key_event(window,key,scancode,action,mods):
    global camera_x
    global camera_y

    speed = 0.1

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

    configBuffer.upload(struct.pack("<fffffI",camera_x, camera_y,1,pos_x , pos_y, len(triangles)))

    compute_clear.dispatch(target.width //8, target.height // 8, 1)
    compute.dispatch(target.width //8, target.height // 8, 1)
    swapchain.present(target)

    stats_buffer.copy_to(stats_buffer_readback)
    print(struct.unpack("<I",stats_buffer_readback.readback(4)))