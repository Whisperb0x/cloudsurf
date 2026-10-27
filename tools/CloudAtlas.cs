using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

// Pack converted cloud textures (square PNGs with alpha, see CloudConvert.cs)
// into an NxN atlas for the VFX Output block (UVMode Atlas, AtlasSize N,N).
// Pixels are copied byte for byte: Graphics.DrawImage works premultiplied and
// would turn fully transparent pixels black, which darkens the mipmaps.
public static class CloudAtlas {
    public static void Run(string[] pngs, string dst, string preview, int cell) {
        int n = (int)Math.Ceiling(Math.Sqrt(pngs.Length));
        int side = n * cell;
        using (var atlas = new Bitmap(side, side, PixelFormat.Format32bppArgb)) {
            var ad = atlas.LockBits(new Rectangle(0, 0, side, side), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            var buf = new byte[ad.Stride * side];
            for (int i = 0; i < buf.Length; i += 4) { buf[i] = 255; buf[i + 1] = 255; buf[i + 2] = 255; buf[i + 3] = 0; }
            for (int k = 0; k < pngs.Length; k++) {
                using (var img = new Bitmap(pngs[k])) {
                    if (img.Width != cell || img.Height != cell)
                        throw new ArgumentException(pngs[k] + " is not " + cell + "x" + cell);
                    var id = img.LockBits(new Rectangle(0, 0, cell, cell), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
                    var src = new byte[id.Stride * cell];
                    Marshal.Copy(id.Scan0, src, 0, src.Length);
                    img.UnlockBits(id);
                    int ox = (k % n) * cell, oy = (k / n) * cell;
                    for (int y = 0; y < cell; y++)
                        Buffer.BlockCopy(src, y * id.Stride, buf, (oy + y) * ad.Stride + ox * 4, cell * 4);
                }
            }
            Marshal.Copy(buf, 0, ad.Scan0, buf.Length);
            atlas.UnlockBits(ad);
            atlas.Save(dst, ImageFormat.Png);
            if (preview != null && preview.Length > 0) {
                var pbuf = new byte[buf.Length];
                for (int i = 0; i < buf.Length; i += 4) {
                    double a = buf[i + 3] / 255.0;
                    pbuf[i] = (byte)(buf[i] * a + 190 * (1 - a));
                    pbuf[i + 1] = (byte)(buf[i + 1] * a + 120 * (1 - a));
                    pbuf[i + 2] = (byte)(buf[i + 2] * a + 70 * (1 - a));
                    pbuf[i + 3] = 255;
                }
                using (var prev = new Bitmap(side, side, PixelFormat.Format32bppArgb)) {
                    var pd = prev.LockBits(new Rectangle(0, 0, side, side), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
                    Marshal.Copy(pbuf, 0, pd.Scan0, pbuf.Length);
                    prev.UnlockBits(pd);
                    prev.Save(preview, ImageFormat.Png);
                }
            }
        }
    }
}
