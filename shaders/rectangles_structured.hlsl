RWTexture2D<float4> Target;

struct Movement {
    float DeltaX;
    float DeltaY;
};
ConstantBuffer<Movement> MovementBuffer;

struct Rectangle{
    float3 Color;
    float2 Position;
    float2 Size;
};
StructuredBuffer<Rectangle> RectangleBuffer;

struct Config {
    int RectanglesNum;
    float3 Color;
};

StructuredBuffer<Config> ConfigBuffer;

[numthreads(8,8,1)]
void main(uint3 tid: SV_DispatchThreadId)
{
    Target[tid.xy] = float4(ConfigBuffer[0].Color,1);
                      
    for(int index=0; index < ConfigBuffer[0].RectanglesNum; index++)
    {
        float2 RectanglePosition = RectangleBuffer[index].Position;
        RectanglePosition.x += MovementBuffer.DeltaX;
        RectanglePosition.y += MovementBuffer.DeltaY;
        float2 RectangleSize = RectangleBuffer[index].Size;
        float3 RectangleColor = RectangleBuffer[index].Color;
                      
        if(tid.x >= RectanglePosition.x && tid.y >= RectanglePosition.y && tid.x < RectanglePosition.x + RectangleSize.x && tid.y < RectanglePosition.y + RectangleSize.y)
        {
            Target[tid.xy] = float4(RectangleColor,1);
        }
    }
}
