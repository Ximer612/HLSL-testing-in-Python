RWTexture2D<float4> Target;
Buffer<float3> VertexBuffer;
Buffer<uint3> IndexBuffer;
Buffer<float3> ColorBuffer;

struct Config {
    float4x4 PerspectiveMatrix;
    float4x4 Camera;
    float4x4 World;
    float DeltaX;
    float DeltaY;
    uint TriangleNum;
};
                      
ConstantBuffer<Config> ConfigBuffer;
RWBuffer<uint> Stats;
                      
float2 NDCtoPixel(float2 Position, uint width, uint height)
{
    const float x = (Position.x + 1) * 0.5 * width;                      
    const float y = (1 - Position.y) * 0.5 * height;      
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
        uint Index0 = IndexBuffer[index].x;
        uint Index1 = IndexBuffer[index].y;
        uint Index2 = IndexBuffer[index].z;
        float4 TrianglePoint0 = mul(float4(VertexBuffer[Index0], 1), ConfigBuffer.World);
        float4 TrianglePoint1 = mul(float4(VertexBuffer[Index1], 1), ConfigBuffer.World);
        float4 TrianglePoint2 = mul(float4(VertexBuffer[Index2], 1), ConfigBuffer.World);
                      
        TrianglePoint0 = mul(TrianglePoint0, ConfigBuffer.Camera);
        TrianglePoint1 = mul(TrianglePoint1, ConfigBuffer.Camera);
        TrianglePoint2 = mul(TrianglePoint2, ConfigBuffer.Camera);
                      
        float4 Point0 = mul(TrianglePoint0, ConfigBuffer.PerspectiveMatrix);
        float4 Point1 = mul(TrianglePoint1, ConfigBuffer.PerspectiveMatrix);
        float4 Point2 = mul(TrianglePoint2, ConfigBuffer.PerspectiveMatrix);
        
        Point0.xyz /= Point0.w;              
        Point1.xyz /= Point1.w;              
        Point2.xyz /= Point2.w;              

        float2 Point0pixel = NDCtoPixel(Point0.xy, width, height);
        float2 Point1pixel = NDCtoPixel(Point1.xy, width, height);
        float2 Point2pixel = NDCtoPixel(Point2.xy, width, height);
     
        float3 BC = barycentric(Point0pixel, Point1pixel, Point2pixel, tid.xy);
        if(BC.x < 0 || BC.y < 0 || BC.z < 0)
        {
            continue;
        }
        else
        {
            Target[tid.xy] = float4(ColorBuffer[index], 1);
            InterlockedAdd(Stats[0], 1);
        }
    }
}