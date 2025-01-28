#version 330 core
out vec4 fragColor;

uniform float iTime;           // Time in seconds
uniform vec2 iResolution;      // Viewport resolution (width, height)
uniform int state;            // State (0 = waiting, 1 = listening, 2 = speaking)
uniform float transitionTime;  // Time since last state change

// Function to generate one layer of particles
vec4 generateLayer(vec2 fragCoord, int targetState, vec3 layerStartColor, vec3 layerEndColor, float layerAlpha) {
    float t = iTime + 5.0;
    float z = 6.0;
    
    int baseParticleCount = 100;
    int particleCount;
    
    if (targetState == 0) {
        particleCount = int(float(baseParticleCount) * 0.25);
    } else if (targetState == 1) {
        particleCount = int(float(baseParticleCount) * 0.50);
    } else {
        particleCount = baseParticleCount;
    }
    
    vec2 s = iResolution.xy;
    vec2 v = z * (2.0 * fragCoord - s) / s.y;
    
    vec3 col = vec3(0.0);
    float sum = 0.0;
    
    float evo = (sin(iTime * 0.01 + 400.0) * 0.5 + 0.5) * 99.0 + 1.0;
    
    // Only generate new particles if this is our target state
    if (state == targetState || abs(transitionTime) < 1.0) {
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
            col = mix(col, mix(layerStartColor, layerEndColor, distRatio), mb/sum);
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
    // Generate each layer with its respective colors
    vec4 waitingLayer = generateLayer(fragCoord, 0, 
        vec3(0.0, 0.0, 1.0),  // Bright blue
        vec3(0.0, 0.0, 0.5),  // Dark blue
        1.0
    );
    
    vec4 listeningLayer = generateLayer(fragCoord, 1,
        vec3(1.0, 0.0, 0.0),  // Bright red
        vec3(0.5, 0.0, 0.0),  // Dark red
        1.0
    );
    
    vec4 speakingLayer = generateLayer(fragCoord, 2,
        vec3(0.0, 1.0, 0.0),  // Bright green
        vec3(0.0, 0.5, 0.0),  // Dark green
        1.0
    );
    
    // Blend the layers together
    vec4 finalOutput = vec4(0.0);
    finalOutput += waitingLayer;
    finalOutput += listeningLayer;
    finalOutput += speakingLayer;
    
    fragColor = finalOutput;
}

void main() {
    mainImage(fragColor, gl_FragCoord.xy);
}