// ABOUTME: 图片处理服务，压缩用户拍照/选取的图片
// ABOUTME: max 1024px，JPEG 0.8 质量，与 Web 版 compressImage 一致

import UIKit

enum CameraService {
    /// 压缩图片到最大 1024px 边长，JPEG 0.8 质量
    static func compressImage(_ image: UIImage, maxDimension: CGFloat = 1024, quality: CGFloat = 0.8) -> Data? {
        let size = image.size
        let scale: CGFloat

        if size.width > maxDimension || size.height > maxDimension {
            scale = maxDimension / max(size.width, size.height)
        } else {
            scale = 1.0
        }

        let newSize = CGSize(width: size.width * scale, height: size.height * scale)

        UIGraphicsBeginImageContextWithOptions(newSize, true, 1.0)
        image.draw(in: CGRect(origin: .zero, size: newSize))
        let resized = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()

        return resized?.jpegData(compressionQuality: quality)
    }
}
