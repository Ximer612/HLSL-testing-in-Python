RWTexture2D<uint64_t> DepthBuffer;

[numthreads(8,8,1)]
void main(uint3 tid: SV_DispatchThreadId)
{      
    DepthBuffer[tid.xy] = 0xFFFFFFFFFFFFFFFF;
}