RWTexture2D<float4> Target;
// Buffer<float3> VertexBuffer;
// Buffer<uint3> IndexBuffer;
Buffer<float3> ColorBuffer;

RWBuffer<uint> Stats;
Texture2D<uint64_t> DepthBuffer;
                      
[numthreads(8,8,1)]
void main(uint3 tid: SV_DispatchThreadId)
{    
    uint64_t VisBuffer = DepthBuffer[tid.xy];
    if(VisBuffer == 0xFFFFFFFFFFFFFFFF)
    {
        return;
    }

    float depth = asfloat((uint)(VisBuffer >> 32));
    uint64_t triangle_index = VisBuffer & 0xFFFFFFFF; // 8 x 0 & 8 x F

    Target[tid.xy] = float4(ColorBuffer[(int)triangle_index], 1); 
    InterlockedAdd(Stats[0], 1);   

}