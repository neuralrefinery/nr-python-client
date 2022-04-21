import numpy as np

def angle2matrix_3ddfa(angles):
    ''' get rotation matrix from three rotation angles(radian). The same as in 3DDFA.
    Args:
        angles: [3,]. x, y, z angles
        x: pitch.
        y: yaw. 
        z: roll. 
    Returns:
        R: 3x3. rotation matrix.
    '''
    # x, y, z = np.deg2rad(angles[0]), np.deg2rad(angles[1]), np.deg2rad(angles[2])
    x, y, z = angles[0], angles[1], angles[2]
    
    # x
    Rx=np.array([[1,      0,       0],
                 [0, np.cos(x),  np.sin(x)],
                 [0, -np.sin(x),   np.cos(x)]])
    # y
    Ry=np.array([[ np.cos(y), 0, -np.sin(y)],
                 [      0, 1,      0],
                 [np.sin(y), 0, np.cos(y)]])
    # z
    Rz=np.array([[np.cos(z), np.sin(z), 0],
                 [-np.sin(z),  np.cos(z), 0],
                 [     0,       0, 1]])
    R = Rx.dot(Ry).dot(Rz)
    return R.astype(np.float32)

def generate_axes( scale, angles, t3d ):

    axes = np.array(
        [[ 0.0, 0.0, 0.0 ],
         [ 1.0, 0.0, 0.0 ],
         [ 0.0, 1.0, 0.0 ],
         [ 0.0, 0.0, 1.0 ]], dtype=np.float32 
    )

    R = angle2matrix_3ddfa( angles )
    
    axes = scale * axes.dot(R.T) + t3d[np.newaxis,:]

    return axes

