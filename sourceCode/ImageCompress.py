import PIL.Image as Image
import os
 
# 图片压缩批处理
# 将待压缩图片放入srcPath中
# 压缩后图片输出到dstPath中
def compressImage(srcPath,dstPath):
    for filename in os.listdir(srcPath):
        if not os.path.exists(dstPath):
                os.makedirs(dstPath)
        srcFile=os.path.join(srcPath,filename)
        dstFile=os.path.join(dstPath,filename)
        if os.path.isfile(srcFile):
            try:
                sImg=Image.open(srcFile)  # 打开图片
                dImg=sImg.resize((239, 320), Image.ANTIALIAS)  # 缩放大小
                for i in range(dImg.size[1]):  # 输出整型像素RGB信息列表
                    print("[" + ", ".join(["0x{:02x}{:02x}{:02x}".format(*dImg.getpixel((j, i))) for j in range(dImg.size[0])]) + "],")
                dImg.save(dstFile)  # 保存图片
                print("Succeeded")
            except Exception:
                print(dstFile + " Failed")
        if os.path.isdir(srcFile):
            compressImage(srcFile, dstFile)
 
if __name__=='__main__':
    compressImage("img_src", "img_dst")
