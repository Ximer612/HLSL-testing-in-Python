RWTexture2D<float4> Target;
RWBuffer<uint> Stats;

struct Movement {
    float DeltaX;
    float DeltaY;
    float2 CameraPosition;
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
    for(int index=0; index < ConfigBuffer[0].RectanglesNum; index++)
    {
        float2 RectanglePosition = RectangleBuffer[index].Position;
        RectanglePosition.x += MovementBuffer.DeltaX;
        RectanglePosition.y += MovementBuffer.DeltaY;
        RectanglePosition.xy += MovementBuffer.CameraPosition;
        float2 RectangleSize = RectangleBuffer[index].Size;
        float3 RectangleColor = RectangleBuffer[index].Color;
                      
        if(tid.x >= RectanglePosition.x && tid.y >= RectanglePosition.y && tid.x < RectanglePosition.x + RectangleSize.x && tid.y < RectanglePosition.y + RectangleSize.y)
        {
            Target[tid.xy] = float4(RectangleColor,1);
            InterlockedAdd(Stats[0],1);
        }
    }
}
