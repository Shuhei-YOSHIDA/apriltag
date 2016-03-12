import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from timeit import default_timer as timer
from collections import OrderedDict
from apriltag_py.utils import DisjointSets, mod2pi, angle_dist, imshow

# %%
fsize2 = (14, 10)
times = OrderedDict()

# %%
cwd = os.getcwd()
image_file = os.path.join(cwd, 'frame0001.png')
color = cv2.imread(image_file, cv2.IMREAD_COLOR)
gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
imshow(color, title='raw')

# %%
# Gaussian blur with downsample
gray_sample = gray

start = timer()
gray_seg = cv2.pyrDown(gray)
times['1_pyrdown'] = timer() - start

imshow(gray_seg, title='seg')

# %%
# Calculate image gradient
scale = 1 / 16.0

start = timer()
Ix = cv2.Scharr(gray_seg, cv2.CV_32F, 1, 0, scale=scale)
Iy = cv2.Scharr(gray_seg, cv2.CV_32F, 0, 1, scale=scale)
times['2_scharr'] = timer() - start

ax1, ax2 = imshow(Ix, Iy, figsize=fsize2, title=('Ix', 'Iy'))

# %%
# Calculate gradient magnitude and angle

start = timer()
im_mag, im_ang = cv2.cartToPolar(Ix, Iy)
times['3_polar'] = timer() - start

imshow(im_mag, im_ang, figsize=fsize2, title=('mag', 'ang'))

# %%
mag_max = np.max(im_mag)
mag_mean = np.mean(im_mag)
mag_median = np.median(im_mag)
mag_meme = (mag_mean + mag_median) / 2.0
f, ax = plt.subplots(figsize=(12, 3))
ax.hist(im_mag.ravel(), 255)
ax.axvline(mag_mean, color='m')
ax.axvline(mag_median, color='r')


# %%
num_pixels = np.size(im_mag)
MIN_MAG = mag_mean
mask = im_mag > MIN_MAG
b = 5

mask[:, :b] = 0
mask[:, -b:] = 0
mask[:b] = 0
mask[-b:] = 0

num_mask = np.count_nonzero(mask)
imshow(mask,  title='mean: {}/{}'.format(num_mask, num_pixels))

# %%
edges = []
h, w = np.shape(im_mag)

start = timer()
mr, mc = np.nonzero(mask)

MAX_ANG_DIFF = np.deg2rad(1)
COST_SCALE = 1024 / MAX_ANG_DIFF

for r, c in zip(mr, mc):
    mag0 = im_mag[r, c]
    ang0 = im_ang[r, c]

    pid0 = r * w + c
    pid1s = (pid0 + 1, pid0 + w, pid0 + w + 1, pid0 + w - 1)

    for pid1 in pid1s:
        mag1 = im_mag.ravel()[pid1]
        ang1 = im_ang.ravel()[pid1]
        cost = 0
        if mag1 < MIN_MAG:
            cost = -1
        else:
            ang_diff = angle_dist(ang0 - ang1)
            if ang_diff > MAX_ANG_DIFF:
                cost = -1
            else:
                cost = int(ang_diff * COST_SCALE)

        if cost >= 0:
            edges.append((pid0, pid1, cost))

t = timer() - start
times['4_calc_edges'] = t

disp_edges = im_mag.copy()
de = disp_edges.ravel()
for e in edges:
    de[e[0]] = mag_max * 2
    de[e[1]] = mag_max * 2

imshow(disp_edges, title='edges')

# %%
# sort edges
start = timer()
edges.sort(key=lambda x: x[-1])
t = timer() - start
times['5_sort_edges'] = t

# %%
# union find
k_ang = 100.0
k_mag = 1200.0

im_mag_vec = im_mag.ravel()
im_ang_vec = im_ang.ravel()
stats = np.vstack((im_mag_vec, im_mag_vec, im_ang_vec, im_ang_vec)).T
dsets = DisjointSets(num_pixels)

for e in edges:
    pid0, pid1, cost = e
    sid0 = dsets.find(pid0)
    sid1 = dsets.find(pid1)
    if sid0 == sid1:
        continue

    size01 = dsets.set_size(sid0) + dsets.set_size(sid1)

    stat0 = stats[sid0]
    stat1 = stats[sid1]

    # get delta in magnitude both segments
    d_mag0 = stat0[1] - stat0[0]
    d_mag1 = stat1[1] - stat1[0]

    # assuming we want to merge these two segments
    # get min and max of merged mag
    min_mag01 = min(stat0[0], stat1[0])
    max_mag01 = max(stat0[1], stat1[1])

    # calculate delta in magnitude for merged segments
    d_mag01 = max_mag01 - min_mag01

    # check with criteria on magnitude
    # M(0 && 1) <= min(D(0), D(1)) + k_mag / size01
    if not d_mag01 <= min(d_mag0, d_mag1) + k_mag / size01:
        continue

    # get delta in angle
    d_ang0 = angle_dist(stat0[3] - stat0[2])
    d_ang1 = angle_dist(stat1[3] - stat1[2])

    # get min and max of merged ang

#    min_ang01 = 0
#    max_ang01 = 0
#    d_ang01 = max_ang01 - min_ang01
#
#    if not d_ang01 <= min(d_ang0, d_ang1) + k_ang / size01:
#        continue

    # union these two sets
#    sid01 = dsets.union(sid0, sid1)
#    stats[sid01] = (min_mag01, max_mag01, min_ang01, max_ang01)


# %%
total_time = 0.0
for key, value in times.iteritems():
    value *= 1e3
    total_time += value
    print(key, value)
print('total', total_time)

plt.show()