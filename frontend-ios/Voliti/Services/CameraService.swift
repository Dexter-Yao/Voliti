// ABOUTME: 图片处理服务，压缩用户拍照/选取的图片
// ABOUTME: max 1024px，JPEG 0.8 质量

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

        let renderer = UIGraphicsImageRenderer(size: newSize)
        let resized = renderer.image { _ in
            image.draw(in: CGRect(origin: .zero, size: newSize))
        }

        return resized.jpegData(compressionQuality: quality)
    }
}
