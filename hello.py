from compushady import Buffer, HEAP_UPLOAD, HEAP_READBACK, HEAP_DEFAULT, Compute
import struct
import compushady.config
from compushady.shaders import hlsl
from compushady.formats import R32_UINT

compushady.config.set_debug(True)

shader = hlsl.compile(""" 
RWBuffer<uint> FastBuffer : register(u0);
                      
[numthreads(8,1,1)]
void main(uint3 tid: SV_DispatchThreadId)
{
    FastBuffer[tid.x] *= 2; 
}
                    """)

source_buffer = Buffer(4*8, HEAP_UPLOAD)
readback_buffer = Buffer(4*8, HEAP_READBACK)
fast_buffer = Buffer(4*8, HEAP_DEFAULT, format=R32_UINT)

data = struct.pack("<IIIIIIII",0,1,2,3,4,5,6,7)

source_buffer.upload(data)
source_buffer.copy_to(fast_buffer)

compute = Compute(shader, uav=[fast_buffer])

compute.dispatch(1,1,1) #quante volte eseguire il blocco di thread

fast_buffer.copy_to(readback_buffer)

print(struct.unpack("<8I",readback_buffer.readback()))