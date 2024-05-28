import glfw
from compushady import Texture2D, Swapchain, Compute, Buffer, HEAP_UPLOAD, HEAP_DEFAULT
from compushady.formats import B8G8R8A8_UNORM
from compushady.shaders import hlsl
from compushady.formats import R32G32B32A32_FLOAT
import struct

import compushady.config
compushady.config.set_debug(True)

rectangles = []

def add_rectangle_buffer(x,y,w,h):
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
    

add_rectangle_buffer(0,0,10,10)
add_rectangle_buffer(10,10,10,10)
add_rectangle_buffer(20,20,10,10)
add_rectangle_buffer(200,10,8,10)
add_rectangle_buffer(10,300,10,100)
add_rectangle_buffer(0,200,10,100)
add_rectangle_buffer(300,300,200,200)

new_fast_buffer = upload_rectangles(rectangles,0,1,0)

shader = hlsl.compile("""
RWTexture2D<float4> Target;
Buffer<float4> RectangleBuffer;

struct Config {
    float DeltaX;
    float DeltaY;
};
                      
ConstantBuffer<Config> ConfigBuffer;
                      
[numthreads(8,8,1)]
void main(uint3 tid: SV_DispatchThreadId)
{
    Target[tid.xy] = float4(1,0,0,1);
                      
    for(int index=0; index < 8; index++)
    for(int index=0; index < asuint(RectangleBuffer[0].r); index++)
    {
        float4 rectangle = RectangleBuffer[1 + index];
        rectangle.x += ConfigBuffer.DeltaX;
        rectangle.y += ConfigBuffer.DeltaY;
                      
        if(tid.x >= rectangle.x && tid.y >= rectangle.y && tid.x < rectangle.x + rectangle.z && tid.y < rectangle.y + rectangle.w)
        {
            Target[tid.xy] = float4(RectangleBuffer[0].yzw,1);
        }
    }
}

""")

configBuffer = Buffer(2*4,HEAP_UPLOAD)

glfw.init()
#disable default opengl gpu access
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)

target = Texture2D(512,512, B8G8R8A8_UNORM)
compute = Compute(shader, uav=[target], srv=[new_fast_buffer], cbv=[configBuffer])

window = glfw.create_window(target.width,target.height, "Simple draw rectangles", None, None)

swapchain = Swapchain(glfw.get_win32_window(window), B8G8R8A8_UNORM,2)

x,y = 0,0

while not glfw.window_should_close(window):
    glfw.poll_events()

    x+=1
    y+=1
    configBuffer.upload(struct.pack("<ff",x,y))

    compute.dispatch(target.width //8, target.height // 8, 1)
    swapchain.present(target)