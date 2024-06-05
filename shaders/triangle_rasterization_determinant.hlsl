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

int det(float2 v1, float2 v2, float2 p)
{
    float2 vpoint = v2 - v1;
    float2 ppoint = p - v1;
    return (vpoint.x * ppoint.y) -(vpoint.y * ppoint.x);
}

bool det_is_point_in_triangle(float2 P, float2 A, float2 B, float2 C)
{
    bool neg_ABP = det(A,B,P) < 0;
    bool neg_BCP = det(B,C,P) < 0;
    bool neg_CAP = det(C,A,P) < 0;
    return (neg_ABP == neg_BCP) && (neg_BCP == neg_CAP);
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

        if(!det_is_point_in_triangle(tid.xy,Point0pixel,Point1pixel,Point2pixel))
        {
            continue;
        }
                    
        Target[tid.xy] = float4(TriangleBuffer[index * 4 + 3], 1.f);
        InterlockedAdd(Stats[0], 1);
    }
}