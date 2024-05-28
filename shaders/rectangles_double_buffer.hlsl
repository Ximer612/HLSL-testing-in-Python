RWTexture2D<float4> Target;
Buffer<float4> RectangleBuffer;
Buffer<float3> ColorsBuffer;

struct Config {
    float DeltaX;
    float DeltaY;
};
                      
ConstantBuffer<Config> ConfigBuffer;
                      
[numthreads(8,8,1)]
void main(uint3 tid: SV_DispatchThreadId)
{
    Target[tid.xy] = float4(RectangleBuffer[0].yzw,1);
                      
    for(int index=0; index < asuint(RectangleBuffer[0].r); index++)
    {
        float4 rectangle = RectangleBuffer[1 + index];
        rectangle.x += ConfigBuffer.DeltaX;
        rectangle.y += ConfigBuffer.DeltaY;
                      
        if(tid.x >= rectangle.x && tid.y >= rectangle.y && tid.x < rectangle.x + rectangle.z && tid.y < rectangle.y + rectangle.w)
        {
            Target[tid.xy] = float4(ColorsBuffer[index],1);
        }
    }
}