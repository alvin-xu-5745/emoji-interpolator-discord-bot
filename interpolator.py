import numpy as np
import colorsys
import requests
import os
import shutil

from PIL import Image

def download_emojis(urls):
    file_paths = []
    for i in range(len(urls)):
        url = urls[i]
        img_data = requests.get(url).content
        fpath = 'tmp/' + url.split('/')[-1]
        with open(fpath, 'wb') as handler:
            handler.write(img_data)
        file_paths.append(fpath)
    return file_paths

def interpolator(urls, weights):
    if not os.path.exists('tmp/'):
        os.mkdir('tmp/')
    images = download_emojis(urls)
    pixels = np.zeros((64, 64, 4))
    transparency_matrix = np.zeros((64, 64))

    # For a given pixel, if any image is above this threshold for alpha then evaluate average on root curve instead of linear
    alpha_threshold = 0.5

    # Forces all images to be RGBA 64x64
    for i in range(len(images)):
        img = Image.open(images[i]).convert('RGBA').resize((64, 64))
        img_pixels = np.asarray(img)
        for r in range(pixels.shape[0]):
            for c in range(pixels.shape[1]):
                pixel = img_pixels[r][c] / 255

                # Average over HLS values
                hls = colorsys.rgb_to_hls(pixel[0], pixel[1], pixel[2])
                pixels[r][c][0] += hls[0] * weights[i]
                pixels[r][c][1] += hls[1] * weights[i]
                pixels[r][c][2] += hls[2] * weights[i]
                pixels[r][c][3] += pixel[3] * weights[i]
                if pixel[3] > alpha_threshold:
                    transparency_matrix[r][c] = 1
    pixels /= sum(weights)

    # Convert back to RGBA, fit transparencies to curve
    for r in range(pixels.shape[0]):
        for c in range(pixels.shape[1]):
            pixel = pixels[r][c]
            rgb = colorsys.hls_to_rgb(pixel[0], pixel[1], pixel[2])
            pixels[r][c][0] = rgb[0] * 255
            pixels[r][c][1] = rgb[1] * 255
            pixels[r][c][2] = rgb[2] * 255
            if transparency_matrix[r][c] == 1:
                pixels[r][c][3] = pixels[r][c][3] ** 0.01
            pixels[r][c][3] *= 255

    # Generate output
    pixels = pixels.astype(np.uint8)
    shutil.rmtree('tmp/', ignore_errors=True)
    return pixels

def get_score(pixels1, pixels2):
    pixels1 = pixels1.astype(np.float16)
    pixels2 = pixels2.astype(np.float16)
    pixel_score = 0
    for r in range(64):
        for c in range(64):
            pixel_score += abs(pixels1[r][c][0] - pixels2[r][c][0]) ** 0.5
            pixel_score += abs(pixels1[r][c][1] - pixels2[r][c][1]) ** 0.5
            pixel_score += abs(pixels1[r][c][2] - pixels2[r][c][2]) ** 0.5
            pixel_score += abs(pixels1[r][c][3] - pixels2[r][c][3]) ** 0.5
    pixel_score /= 64 * 64
    return pixel_score

    
