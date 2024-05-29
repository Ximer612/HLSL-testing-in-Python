RWTexture2D<float4> Target;
RWBuffer<uint> Stats;

struct Config {
    int RectanglesNum;
    float3 Color;
};

StructuredBuffer<Config> ConfigBuffer;

[numthreads(8,8,1)]
void main(uint3 tid: SV_DispatchThreadId)
{
    Target[tid.xy] = float4(ConfigBuffer[0].Color,1);
    Stats[0] = 0;
}