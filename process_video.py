import numpy as np
import math
import cv2
import sys
import os

#base to detect when a frame is a gameplay
if not os.path.exists( 'base.png' ):
	print( 'the file base.png doesnt exists' )
	quit()

if len( sys.argv ) is not 2:
	print( 'Usage: python process_video.py <videofile.mp4>' )
	quit()

cap = cv2.VideoCapture( sys.argv[1] )
fps = math.ceil( cap.get( cv2.CAP_PROP_FPS ) )

fourcc = cv2.VideoWriter_fourcc(*'FMP4')
framesize = ( cap.get( cv2.CAP_PROP_FRAME_WIDTH ), cap.get( cv2.CAP_PROP_FRAME_HEIGHT ) )

line = []
base = cv2.imread( 'base.png' )
for h in base: line.append( h[10] )
line = np.array( line )


c = 0
ini = 0
games = []
started = False
while( cap.isOpened() ):
	ret, frame = cap.read()
	if not ret: break
	c += 1

	line2 = []
	for h in frame: line2.append( h[10] )
	line2 = np.array( line2 )

	diff = np.mean( cv2.absdiff( line, line2 ) )
	if diff > 10:
		if started:
			started = False
			#out.release()
			games.append( ( ini, c ) )
			print( '.' )

		continue

	if not started:
		started = True
		#out = cv2.VideoWriter( 'frame_'+str(c)+'.mp4', fourcc, fps, framesize )
		ini = c

	#out.write( frame )


cap.release()
cv2.destroyAllWindows()

games_time = []
for (ini,end) in games:
	if end-ini < 60*90:
		#too short. maybe a repetition
		if os.path.exists( 'frame_'+str( ini )+'.mp4' ):
			os.remove( 'frame_'+str( ini )+'.mp4' )
		continue

	m_ini = math.floor( ini/3600 )
	s_ini = math.ceil( (ini/60)-(m_ini*60) )

	m_fin = math.floor( fin/3600 )
	s_fin = math.ceil( (fin/60)-(m_fin*60) )

	games_time.append( str( m_ini )+':'+str( s_ini )+' - '+str( m_fin )+':'+str( s_fin ) )

print( games_time )
