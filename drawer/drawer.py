import cv2
import numpy as np

from . import keypoints_data
from . import tools

from matplotlib import pyplot as pp

class drawer :
    def _write_text( self, image, label, p, font_scale = 0.5, bg_color=(0, 0, 255), label_color=(0, 0, 0) ):
        FONT = cv2.FONT_HERSHEY_SIMPLEX
        FONT_SCALE = font_scale

        (label_width, label_height), baseline = cv2.getTextSize(label, FONT, FONT_SCALE, 2)
        cv2.rectangle( image, (p[0],p[1]), (p[0]+label_width, p[1]+label_height+baseline), bg_color, cv2.FILLED )
        cv2.putText( image, label, (p[0],p[1]+label_height), FONT, FONT_SCALE, label_color)

        return label_height + baseline

    def _draw_log( self, image, meta, show_scores=True, title_y_loc=0 ):
        y_loc = 0

        print( meta.keys() )

        if 'objects' in meta :
            for obj in meta['objects'] :
                obj_type = obj['class']

                if 'roi' in obj :
                    b_raw = np.array(obj['roi'])/self._scale

                    b_width = b_raw[2] - b_raw[0]
                    b_height = b_raw[3] - b_raw[1]
                    b = np.round(b_raw).astype(np.int32)
                    box_valid = int(obj['valid'])

                    str = '%s %.2f' % ( obj_type, obj['score'])

                    if box_valid == 1 :
                        cv2.rectangle( image, (b[0],b[1]), (b[2],b[3]), (0,0,int(255 * obj['score'])), 2 )
                    else :
                        cv2.rectangle( image, (b[0],b[1]), (b[2],b[3]), (int(255 * obj['score']),0,0), 2 )
                    #cv2.putText(image, str, (b[0],b[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255),3)

                    y_loc = 0

                    if show_scores :
                        y_loc += self._write_text( image, str, (b[2],b[1] + y_loc) )

                    if 'variables' in obj :
                        for key, item in obj["variables"].items() :
                            var_str = '%s %g' % ( key, round(item,5) )
                            y_loc += self._write_text(image, var_str, (b[2],b[1] + y_loc))

                    if 'attributes' in obj :
                        for key, item in obj["attributes"].items() :
                            var_str = '%s %s' % ( key, item )
                            y_loc += self._write_text(image, var_str, (b[2],b[1] + y_loc))

                    if 'garments' in obj :
                        for garment in obj['garments'] :
                            gb = np.round(np.array(garment['roi'])/self._scale).astype(np.int32)
                            str = '%s %.2f' % ( garment['type'], garment['score'])
                            cv2.rectangle( image, (gb[0],gb[1]), (gb[2],gb[3]), (255,0,0), 2 )

                            garment_y_loc = 0

                            if show_scores :
                                garment_y_loc += self._write_text( image, str, (gb[2],gb[1] + garment_y_loc), bg_color=(255,0,0) )

                    if 'keypoints' in obj :
                        keypoints = np.array(obj['keypoints'])

                        x_arr = np.round(keypoints[:,0] / self._scale).astype( int )
                        y_arr = np.round(keypoints[:,1] / self._scale).astype( int )
                        visible = keypoints[:,2]
                        valid = keypoints[:,3]

                        # Drawing lines if the object type is person
                        if obj_type == "person" :
                            for pair in keypoints_data.coco_pairs :
                                v0 = visible[ pair[0] ]
                                v1 = visible[ pair[1] ]

                                if v0 >= 0.15 and v1 >= 0.15 :
                                    x0, y0 = x_arr[ pair[0] ], y_arr[ pair[0] ]
                                    x1, y1 = x_arr[ pair[1] ], y_arr[ pair[1] ]
                                    cv2.line( image, (x0,y0), (x1,y1), (0,0,255), 2 )

                        # Drawing the keypoints
                        for x,y,vi, val in zip( x_arr, y_arr, visible, valid ):
                            if vi > 0.15 :
                                if val == 1.0 :
                                    cv2.circle( image, (x,y), 5, (0,int(255*vi),0),2)
                                else :
                                    cv2.circle( image, (x,y), 5, (255,0,0),2)


                    if 'keypoints3d' in obj :
                        keypoints3d = np.array(obj['keypoints3d'])
                        x_arr = np.round(keypoints3d[:,0] / self._scale).astype( int )
                        y_arr = np.round(keypoints3d[:,1] / self._scale).astype( int )
                        z_arr = np.round(keypoints3d[:,2] / self._scale).astype( int )

                        # Drawing the keypoints
                        for x,y in zip( x_arr, y_arr ):
                            cv2.circle( image, (x,y), 5, (0,255,0),2)

                    if 'center3d' in obj :
                        center3d = np.array(obj['center3d'])
                        x = np.round(center3d[0] / self._scale).astype( int )
                        y = np.round(center3d[1] / self._scale).astype( int )
                        z = np.round(center3d[2] / self._scale).astype( int )

                        cv2.circle(image, (x,y), 5, (255,0,0),2)

                        pitch = obj['variables']['pitch'] * -1
                        roll = obj['variables']['roll'] * -1
                        yaw = obj['variables']['yaw']

                        axes = tools.generate_axes( b_height, (pitch, yaw, roll), center3d/self._scale )
                        axes = np.round( axes ).astype(int)

                        c = axes[0]
                        x = axes[1]
                        y = axes[2]
                        z = axes[3]

                        cv2.line(image,(c[0], c[1]),(x[0], x[1]),(0,0,255),2)
                        cv2.line(image,(c[0], c[1]),(y[0], y[1]),(0,255,0),2)
                        cv2.line(image,(c[0], c[1]),(z[0], z[1]),(255,0,0),2)



        title_y_loc += self._write_text( image, "Log", (0,title_y_loc), font_scale=0.5, bg_color=(255,255,255) )

        if 'region' in meta :
            x0 = int(meta['region'][0] / self._scale)
            y0 = int(meta['region'][1] / self._scale)
            x1 = int(meta['region'][2] / self._scale)
            y1 = int(meta['region'][3] / self._scale)

            cv2.rectangle( image, (x0,y0), (x1,y1), (255,255,0), 2 )

        if 'variables' in meta :
            for key, item in meta['variables'].items() :
                variable_str = "Variable - %s : %g" % ( key, item )
                title_y_loc += self._write_text( image, variable_str, (0,title_y_loc), font_scale=0.5, bg_color=(255,255,255) )

        return image, title_y_loc

    def _draw_message( self, image, meta, show_scores=True, title_y_loc=0 ):
        title_y_loc += self._write_text( image, "Message : %s" % (meta), (0,title_y_loc), font_scale=0.5, bg_color=(255,255,255) )
        return image, title_y_loc

    def _draw_output( self, image, meta, show_scores=True ):
        title_y_loc = 0

        if 'log' in meta :
            image, title_y_loc = self._draw_log( image, meta['log'], show_scores=show_scores )
        if 'message' in meta :
            image, title_y_loc = self._draw_message( image, meta['message'], title_y_loc )
    
        return image

    def _draw_count( self, image, meta, show_scores=True ):
        count = meta.get('count',None)
        label = 'Count : %d' % ( count )

        if 'detections' in meta :
            for obj in meta['detections'] :
                obj_type = obj['type']
                if 'roi' in obj :
                    b = np.round(np.array(obj['roi'])/self._scale).astype(np.int32)

                    det_score = obj['score']
                    str = '%s %.2f' % ( obj_type, det_score)
                    cv2.rectangle( image, (b[0],b[1]), (b[2],b[3]), (0,0,255), 3 )
                    #cv2.putText(image, str, (b[0],b[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255),3)

                    y_loc = 0
                    if show_scores :
                        y_loc += self._write_text(image, str, (b[0],b[1]))

        self._write_text( image, label, (0,0), font_scale=2, bg_color=(255,255,255) )

        return image

    def _draw_region_check( self, image, meta, show_scores=True ):
        if 'detections' in meta :
            for obj in meta['detections'] :
                obj_type = obj['type']
                if 'roi' in obj :
                    b = np.round(np.array(obj['roi'])/self._scale).astype(np.int32)

                    det_score = obj['score']
                    str = '%s %.2f' % ( obj_type, det_score)
                    cv2.rectangle( image, (b[0],b[1]), (b[2],b[3]), (255,0,0), 3 )
                    #cv2.putText(image, str, (b[0],b[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255),3)

                    if show_scores :
                        self._write_text(image, str, (b[0],b[1]))

        if 'regions' in meta :
            colors = {}
            colors[0] = (0,0,255)
            colors[1] = (0,255,0)
            for obj in meta['regions'] :
                b = np.round(np.array(obj['roi'])/self._scale).astype(np.int32)
                n = obj['name']
                c = obj['check']

                cv2.rectangle( image, (b[0],b[1]), (b[2],b[3]), colors[c], 3 )
                self._write_text(image, n, (b[0],b[1]))

        return image

    def _draw_engagement( self, image, meta, show_scores=True ):
        if 'detections' in meta :

            colors = {}
            colors[0] = (0,0,255)
            colors[1] = (0,255,0)

            for obj in meta['detections'] :
                obj_type = obj['type']
                if 'roi' in obj :
                    b = np.round(np.array(obj['roi'])/self._scale).astype(np.int32)

                    det_score = obj['score']
                    engaged = obj['engaged']

                    str = '%s %.2f' % ( obj_type, det_score)
                    cv2.rectangle( image, (b[0],b[1]), (b[2],b[3]), colors[engaged], 3 )
                    #cv2.putText(image, str, (b[0],b[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255),3)

                    if show_scores :
                        self._write_text(image, str, (b[0],b[1]))

        label = 'Egagement %g' % ( meta['engagement'] )
        self._write_text( image, label, (0,0), font_scale=2, bg_color=(255,255,255) )

        return image

    def _draw_content( self, image, meta, show_scores=True ):
        cname = meta.get('ContentName','noface.jpg')
        return self._assets[ cname ]

    def __init__( self, upload_scale, draw_scale ):
        self._upload_scale = upload_scale
        self._draw_scale = draw_scale
        self._scale = upload_scale / draw_scale
        self._draw = {}
        self._draw['log'] = self._draw_log
        self._draw['message'] = self._draw_message

        self._assets = {}
        #self._assets['noface.jpg'] = cv2.imread('assets/noface.jpg')
        #self._assets['female.jpg'] = cv2.imread('assets/female.jpg')
        #self._assets['male.jpg'] = cv2.imread('assets/male.jpg')
        #self._assets['group.jpg'] = cv2.imread('assets/group.jpg')

    def draw( self, image_src, meta, show_scores=True, use_image=False ):

        if use_image :
            image = image_src
        else :
            image = np.zeros_like( image_src )

        image = cv2.resize(image, None, None, self._draw_scale, self._draw_scale)

        data = meta.get("data", {})

        title_y_loc = 0

        for key, item in data.items() :
            if key in self._draw :
                image, title_y_loc_ = self._draw[key]( image, item, show_scores=show_scores, title_y_loc=title_y_loc )
                title_y_loc += title_y_loc_

        #if type is not None :
        #    if type in self._draw :
        #        image = self._draw[type]( image, meta['data'], show_scores=show_scores )

        return image
