#version 330 core
out vec4 fragColor;

uniform float iTime;           // Time in seconds
uniform vec2 iResolution;      // Viewport resolution (width, height)
uniform int state;             // State (0 = waiting, 1 = listening, 2 = speaking)

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float t = iTime + 5.0;
    float z = 6.0;

    const int n = 100;

    vec3 startColor = vec3(0.0, 0.64, 0.2);
    vec3 endColor = vec3(0.06, 0.35, 0.85);

    float startRadius = 0.84;
    float endRadius = 1.6;

    float power = 0.51;
    float duration = 4.0;

    vec2 s = iResolution.xy;
    vec2 v = z * (2.0 * fragCoord - s) / s.y;

    if (state == 1) { // Listening state
        v *= 1.2; // Example: Modify visuals for listening state
    } else if (state == 2) { // Speaking state
        v *= 0.8; // Example: Modify visuals for speaking state
    }

    vec3 col = vec3(0.0);
    vec2 pm = v.yx * 2.8;
    float dMax = duration;

    float evo = (sin(iTime * 0.01 + 400.0) * 0.5 + 0.5) * 99.0 + 1.0;
    float mb = 0.0;
    float mbRadius = 0.0;
    float sum = 0.0;

    for (int i = 0; i < n; i++) {
        float d = fract(t * power + 48934.4238 * sin(float(i / int(evo)) * 692.7398));
        float tt = 0.0;
        float a = 6.28 * float(i) / float(n);
        float x = d * cos(a) * duration;
        float y = d * sin(a) * duration;
        float distRatio = d / dMax;
        mbRadius = mix(startRadius, endRadius, distRatio);
        vec2 p = v - vec2(x, y);
        mb = mbRadius / dot(p, p);
        sum += mb;
        col = mix(col, mix(startColor, endColor, distRatio), mb / sum);
    }

    sum /= float(n);
    col = normalize(col) * sum;
    sum = clamp(sum, 0.0, 0.4);
    vec3 tex = vec3(1.0);
    col *= smoothstep(tex, vec3(0.0), vec3(sum));
    fragColor = vec4(col, 1.0);
}

void main() {
    mainImage(fragColor, gl_FragCoord.xy);
}