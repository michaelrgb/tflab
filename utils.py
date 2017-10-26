import tensorflow as tf, numpy as np
DTYPE = tf.float32

def wrapList(value):
    return value if type(value) == list else [value]

def variable_summaries(var):
    tf.summary.scalar('min', tf.reduce_min(var))
    tf.summary.scalar('max', tf.reduce_max(var))
    mean = tf.reduce_mean(var)
    tf.summary.scalar('mean', mean)
    stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
    tf.summary.scalar('stddev', stddev)
    tf.summary.histogram('histogram', var)

def conv2d(x, W, stride=1, padding='VALID'):
    return tf.nn.conv2d(x, W, strides=[1, stride, stride, 1], padding=padding)
def max_pool(x, size=4, stride=1, padding='VALID'):
    return tf.nn.max_pool(x, ksize=[1, size, size, 1],
                          strides=[1, stride, stride, 1], padding=padding)
def lrelu(x):
    return tf.maximum(x, x*0.01)

def weight_variable(shape, init_zeros=False):
    return tf.Variable(initial_value=tf.zeros(shape) if init_zeros else tf.truncated_normal(shape, stddev=0.1, seed=0))

def imshow(imlist):
    import matplotlib.pyplot as plt
    kwargs = {'interpolation': 'nearest'}
    plt.close()
    imlist = wrapList(imlist)
    f, axarr = plt.subplots(len(imlist))
    #axarr = wrapList(axarr)# Not list if only 1 image
    for i, nparray in enumerate(imlist):
        shape = nparray.shape
        if shape[-1] == 1:
            # If its greyscale then remove the 3rd dimension if any
            nparray = nparray.reshape((shape[0], shape[1]))
            # Plot negative pixels on the blue channel
            kwargs['cmap'] = 'bwr'
            kwargs['vmin'] = -1.
            kwargs['vmax'] = 1.
        ax = axarr[i] if len(imlist) > 1 else axarr
        im = ax.imshow(nparray, **kwargs)
        f.colorbar(im, ax=ax)
    f.show()

def gaussian_filter(kernel_size):
    x = np.zeros((kernel_size, kernel_size, 1, 1), dtype=DTYPE.name)

    def gauss(x, y, sigma=2.0):
        Z = 2 * np.pi * sigma ** 2
        return 1. / Z * np.exp(-(x ** 2 + y ** 2) / (2. * sigma ** 2))

    mid = np.floor(kernel_size / 2.)
    for i in xrange(0, kernel_size):
        for j in xrange(0, kernel_size):
            x[i, j, 0, 0] = gauss(i - mid, j - mid)

    weights = x / np.sum(x)
    return tf.constant(weights, DTYPE)

def local_contrast_norm(x, gaussian_weights):
    # Move the input channels into the batches
    shape = tf.shape(x)
    x = tf.transpose(x, [0, 3, 1, 2])
    x = tf.reshape(x, [shape[0]*shape[3], shape[1], shape[2], 1])

    # For each pixel, remove local mean
    mean = conv2d(x, gaussian_weights, padding='SAME')
    mean_subtracted = x - mean

    # Calculate local standard deviation
    local_stddev = tf.sqrt(conv2d(mean_subtracted**2, gaussian_weights, padding='SAME'))

    # Lower gives more noise in areas of low contrast, i.e. non-edges
    threshold = 1e-1

    # Divide by the local stddev, with threshold to prevent divide-by-0
    local_stddev = tf.maximum(local_stddev, threshold)
    x = mean_subtracted / local_stddev

    # Rescale to [0 1]
    x = tf.maximum(x, 0.)
    x /= tf.maximum(tf.reduce_max(x, axis=[1, 2], keep_dims=True), threshold)

    # Restore the input channels
    x = tf.reshape(x, [shape[0], shape[3], shape[1], shape[2]])
    x = tf.transpose(x, [0, 2, 3, 1])
    return x
