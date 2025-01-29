#version 330 core
out vec4 fragColor;

uniform float iTime;
uniform vec2 iResolution;

struct State {
    bool enabled;
    vec3 color;
};

uniform State states[4];  // waiting, listening, speaking, thinking

vec4 generateLayer(vec2 fragCoord, int idx, vec3 color, float layerAlpha) {
    float t = iTime + 5.0;
    float z = 6.0;
    
    int baseParticleCount = 100;
    int particleCount = int(float(baseParticleCount) * (idx == 3 ? 2.5 : idx == 2 ? 1.0 : idx == 1 ? 0.5 : 0.15));
    
    vec2 s = iResolution.xy;
    vec2 v = z * (2.0 * fragCoord - s) / s.y;
    
    vec3 col = vec3(0.0);
    float sum = 0.0;
    
    float evo = (sin(iTime * 0.01 + 400.0) * 0.5 + 0.5) * 99.0 + 1.0;
    
    // Special handling for waiting state (idx 0)
    bool shouldRender = idx == 0 ? 
        (states[idx].enabled && !states[1].enabled && !states[2].enabled && !states[3].enabled) : 
        states[idx].enabled;
    
    if (shouldRender) {
        for(int i = 0; i < baseParticleCount; i++) {
            if (i >= particleCount) break;
            
            float d = fract(t * 0.51 + 48934.4238 * sin(float(i/int(evo)) * 692.7398));
            float a = 6.28 * float(i) / float(particleCount);
            float x = d * cos(a) * 4.0;
            float y = d * sin(a) * 4.0;
            
            float distRatio = d / 4.0;
            float mbRadius = mix(0.84, 1.6, distRatio);
            
            vec2 p = v - vec2(x, y);
            float mb = mbRadius / dot(p, p);
            
            sum += mb;
            col = mix(col, mix(color, color * 0.5, distRatio), mb/sum);
        }
        
        sum /= float(particleCount);
        col = normalize(col) * sum;
        sum = clamp(sum, 0.0, 0.4);
        
        col *= smoothstep(vec3(1.0), vec3(0.0), vec3(sum));
        return vec4(col, layerAlpha * sum);
    }
    
    return vec4(0.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec4 finalOutput = vec4(0.0);
    
    for(int i = 0; i < 4; i++) {
        finalOutput += generateLayer(fragCoord, i, states[i].color, 1.0);
    }
    
    fragColor = finalOutput;
}

void main() {
    mainImage(fragColor, gl_FragCoord.xy);
}