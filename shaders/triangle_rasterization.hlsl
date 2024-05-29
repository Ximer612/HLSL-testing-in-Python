RWTexture2D<float4> Target;
Buffer<float3> TriangleBuffer;

struct Config {
    float3 Camera;
    float DeltaX;
    float DeltaY;
    uint TriangleNum;
};
                      
ConstantBuffer<Config> ConfigBuffer;
RWBuffer<uint> Stats;
                      
float2 NDCtoPixel(float2 Position, uint width, uint height)
{
    float x = (Position.x + 1) * 0.5 * width;                      
    float y = (1 - Position.y) * 0.5 * height;      
    return float2(x, y);
}              

float3 barycentric(float2 a, float2 b, float2 c, float2 p)
{
    float3 x = float3(c.x - a.x, b.x - a.x, a.x - p.x);
    float3 y = float3(c.y - a.y, b.y - a.y, a.y - p.y);
    float3 u = cross(x, y);

    if (abs(u.z) < 1.0)
    {
        return float3(-1, 1, 1);
    }

    return float3(1.0 - (u.x+u.y)/u.z, u.y/u.z, u.x/u.z);
}
                      
[numthreads(8,8,1)]
void main(uint3 tid: SV_DispatchThreadId)
{      
    uint width;
    uint height;
    Target.GetDimensions(width, height);    

    for(int index = 0; index < ConfigBuffer.TriangleNum; index++)
    {
        float3 TrianglePoint0 = TriangleBuffer[index * 4];
        float3 TrianglePoint1 = TriangleBuffer[index * 4 + 1];
        float3 TrianglePoint2 = TriangleBuffer[index * 4 + 2];
    
        TrianglePoint0 += ConfigBuffer.Camera;
        TrianglePoint1 += ConfigBuffer.Camera;
        TrianglePoint2 += ConfigBuffer.Camera;
        
        float2 Point0pixel = NDCtoPixel(TrianglePoint0.xy, width, height);
        float2 Point1pixel = NDCtoPixel(TrianglePoint1.xy, width, height);
        float2 Point2pixel = NDCtoPixel(TrianglePoint2.xy, width, height);
     
        float3 bc = barycentric(Point0pixel,Point1pixel,Point2pixel, tid.xy);             
        if(bc.x < 0 || bc.y < 0 || bc.z < 0)
        {
            continue;
        }
                    
        Target[tid.xy] = float4(TriangleBuffer[index * 4 + 3], 1.f);
        InterlockedAdd(Stats[0], 1);
    }
}