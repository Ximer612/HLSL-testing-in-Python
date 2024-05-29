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

uint2 NDCtoPixel(float2 Position, uint width, uint height)
{
    uint x = (Position.x + 1) * 0.5 * width;
    uint y = (1 - Position.y) * 0.5 * height;

    return uint2(x,y);
}

[numthreads(8,8,1)]
void main(uint3 tid: SV_DispatchThreadId)
{
    uint width;
    uint height;
    Target.GetDimensions(width, height);

    for(int index=0; index < ConfigBuffer[0].RectanglesNum; index++)
    {
        float2 RectanglePosition = RectangleBuffer[index].Position;
        RectanglePosition.x += MovementBuffer.DeltaX;
        RectanglePosition.y += MovementBuffer.DeltaY;
        RectanglePosition.xy += MovementBuffer.CameraPosition;
        float2 RectangleSize = RectangleBuffer[index].Size;
        float3 RectangleColor = RectangleBuffer[index].Color;
        uint2 PixelPos = NDCtoPixel(RectanglePosition,width,height);
        uint2 PixelSize = NDCtoPixel(RectangleSize,width,height);
                      
        if(tid.x >= PixelPos.x && tid.y >= PixelPos.y && tid.x < PixelPos.x + PixelSize.x && tid.y < PixelPos.y + PixelSize.y)
        {
            Target[tid.xy] = float4(RectangleColor,1);
            InterlockedAdd(Stats[0],1);
        }
    }
}
