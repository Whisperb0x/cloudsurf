using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class CloudConvert {
    public static double Lift = 0.6;  // 0 = photo shading, 1 = flat white
    public static int OutSize = 0;    // >0: shrink the square result to this size (integer factor)

    // Box-filter shrink; colour is averaged weighted by alpha so transparent
    // (white) pixels don't wash out or darken the edges.
    static byte[] Shrink(byte[] src, int side, int stride, int outSize, out int outStride) {
        int f = side / outSize;
        outStride = outSize * 4;
        var dst = new byte[outStride * outSize];
        for (int y = 0; y < outSize; y++) for (int x = 0; x < outSize; x++) {
            double sa = 0, sr = 0, sg = 0, sb = 0;
            for (int j = 0; j < f; j++) for (int i = 0; i < f; i++) {
                int si = (y * f + j) * stride + (x * f + i) * 4;
                double a = src[si + 3] / 255.0;
                sa += a; sb += src[si] * a; sg += src[si + 1] * a; sr += src[si + 2] * a;
            }
            int di = y * outStride + x * 4;
            if (sa > 0) {
                dst[di] = (byte)(sb / sa); dst[di + 1] = (byte)(sg / sa); dst[di + 2] = (byte)(sr / sa);
            } else {
                dst[di] = 255; dst[di + 1] = 255; dst[di + 2] = 255;
            }
            dst[di + 3] = (byte)(sa / (f * f) * 255);
        }
        return dst;
    }
    public static void Run(string src, string dst, string preview, double white, double black, double gamma) {
        using (var img = new Bitmap(src)) {
            int side = Math.Max(img.Width, img.Height);
            int ox = (side - img.Width) / 2, oy = (side - img.Height) / 2;
            var output = new Bitmap(side, side, PixelFormat.Format32bppArgb);
            var prev = new Bitmap(side, side, PixelFormat.Format32bppArgb);
            var inData = img.LockBits(new Rectangle(0, 0, img.Width, img.Height), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            var outData = output.LockBits(new Rectangle(0, 0, side, side), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            var prevData = prev.LockBits(new Rectangle(0, 0, side, side), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            var src32 = new byte[inData.Stride * img.Height];
            Marshal.Copy(inData.Scan0, src32, 0, src32.Length);
            // Transparent pixels are white, not black: the sim's mipmaps blend
            // colour regardless of alpha, and black there turns distant puffs grey.
            var dst32 = new byte[outData.Stride * side];
            for (int i = 0; i < dst32.Length; i += 4) { dst32[i] = 255; dst32[i + 1] = 255; dst32[i + 2] = 255; dst32[i + 3] = 0; }
            var pv32 = new byte[prevData.Stride * side];
            for (int y = 0; y < side; y++) for (int x = 0; x < side; x++) {
                int pi = y * prevData.Stride + x * 4;
                pv32[pi] = 190; pv32[pi + 1] = 120; pv32[pi + 2] = 70; pv32[pi + 3] = 255;  // sky blue (BGRA)
            }
            for (int y = 0; y < img.Height; y++) {
                for (int x = 0; x < img.Width; x++) {
                    int si = y * inData.Stride + x * 4;
                    double b = src32[si] / 255.0, g = src32[si + 1] / 255.0, r = src32[si + 2] / 255.0;
                    double lum = Math.Max(r, Math.Max(g, b));
                    double a = Math.Min(1.0, Math.Max(0.0, (lum - black) / (white - black)));
                    a = Math.Pow(a, gamma);
                    int di = (y + oy) * outData.Stride + (x + ox) * 4;
                    if (a <= 0.004) continue;
                    // un-premultiply from black, then lift towards white: the sim
                    // lights the particles itself, baked shadow would double up
                    double inv = 1.0 / Math.Max(a, 0.05);
                    double rr = Math.Min(1.0, r * inv), gg = Math.Min(1.0, g * inv), bb = Math.Min(1.0, b * inv);
                    rr += (1.0 - rr) * Lift; gg += (1.0 - gg) * Lift; bb += (1.0 - bb) * Lift;
                    dst32[di] = (byte)(bb * 255); dst32[di + 1] = (byte)(gg * 255);
                    dst32[di + 2] = (byte)(rr * 255); dst32[di + 3] = (byte)(a * 255);
                    pv32[di] = (byte)(bb * 255 * a + 190 * (1 - a));
                    pv32[di + 1] = (byte)(gg * 255 * a + 120 * (1 - a));
                    pv32[di + 2] = (byte)(rr * 255 * a + 70 * (1 - a));
                }
            }
            Marshal.Copy(dst32, 0, outData.Scan0, dst32.Length);
            Marshal.Copy(pv32, 0, prevData.Scan0, pv32.Length);
            img.UnlockBits(inData); output.UnlockBits(outData); prev.UnlockBits(prevData);
            if (OutSize > 0 && OutSize < side && side % OutSize == 0) {
                int os;
                var small = Shrink(dst32, side, outData.Stride, OutSize, out os);
                using (var sm = new Bitmap(OutSize, OutSize, PixelFormat.Format32bppArgb)) {
                    var sd = sm.LockBits(new Rectangle(0, 0, OutSize, OutSize), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
                    for (int y = 0; y < OutSize; y++)
                        Marshal.Copy(small, y * os, sd.Scan0 + y * sd.Stride, os);
                    sm.UnlockBits(sd);
                    sm.Save(dst, ImageFormat.Png);
                }
            } else {
                output.Save(dst, ImageFormat.Png);
            }
            if (preview.Length > 0) prev.Save(preview, ImageFormat.Png);
            output.Dispose(); prev.Dispose();
        }
    }
}
