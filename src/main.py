#!/usr/bin/python
import RPi.GPIO as GPIO
import time, multiprocessing, Queue, json, base64
import cv2

GPIO.setmode(GPIO.BCM)

###################
def Distance_test(TrigPin, EchoPin):
    GPIO.output(TrigPin,GPIO.HIGH)
    time.sleep(0.000015)
    GPIO.output(TrigPin,GPIO.LOW)
    while not GPIO.input(EchoPin):
        pass
    t1 = time.time()
    while GPIO.input(EchoPin):
        pass
    t2 = time.time()
    print "distance is %d " % (((t2 - t1)* 340 / 2) * 100)
    time.sleep(0.01)
    return ((t2 - t1)* 340 / 2) * 100

def checkresult(res):
    for i in res['Results']:
        for j in i['Candidates']:
            print j['Score']
            if 85 < j['Score']:
                return True
    return False

def addpic(img1,img2):
    #
    rows, cols = img2.shape[:2]
    roi = img1[:rows, :cols]

    #
    img2gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(img2gray, 220, 255, 3) #cv2.THRESH_BINARY
    mask_inv = cv2.bitwise_not(mask)

    #
    img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
    dst = cv2.add(img1_bg, img2)
    img1[:rows, :cols] = dst
    return img1

def showvideo( logo_checking, logo_fail, logo_succ, logo_error, picsave, q):
    # init
    l_ck = cv2.imread( logo_checking)
    l_fa = cv2.imread( logo_fail)
    l_su = cv2.imread( logo_succ)
    l_er = cv2.imread( logo_error)

    wname='show'
    cv2.namedWindow(wname, 0);
    cv2.namedWindow(wname, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(wname, 0, 1) #(wname, cv2.WND_PROP_FULLSCREEN, cv2.cv.WINDOW_FULLSCREEN)

    cap = cv2.VideoCapture(0)

    # start show
    flag = 'f.0'
    nflag = ''
    while(1): 
        # get a frame 
        ret, frame = cap.read() 
        # get message
        try:
            nflag = q.get(block = False)
            print nflag
            # save pic
            if 'pic' == nflag:
                cv2.imwrite( picsave, frame)
            else:
                flag = nflag
        except Queue.Empty as e:
            pass
        # review frame
        if 'f.0' == flag:
            pass
        elif 'f.1' == flag:
           frame = addpic( frame, l_ck)
        elif 'f.2' == flag:
            frame = addpic( frame, l_fa)
        elif 'f.3' == flag:
            frame = addpic( frame, l_su)
        elif 'f.4' == flag:
            frame = addpic( frame, l_er)
        else:
            font = cv2.FONT_HERSHEY_DUPLEX
            frame = cv2.putText(frame, flag, (0, 0), font, 1, (255, 0, 0), 2,)        
        # show a frame 
        cv2.imshow(wname, frame) 
        #cv2.waitKey(1)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    return ''

def checking(picpath, sid, skey):
    # search person
    fdata=open(picpath).read()
    pic_b64=base64.b64encode(fdata)

    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException 
    from tencentcloud.iai.v20180301 import iai_client, models 
    try: 
        cred = credential.Credential(sid, skey) 
        httpProfile = HttpProfile()
        httpProfile.endpoint = "iai.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = iai_client.IaiClient(cred, "", clientProfile) 

        req = models.SearchFacesRequest()
        params = '{"GroupIds":["test_001"],"Image":"%s","MaxFaceNum":10}'%pic_b64
        req.from_json_string(params)

        resp = client.SearchFaces(req) 
        return True, json.loads(resp.to_json_string())

    except TencentCloudSDKException as err: 
        print(err)
        return False, err

# error put
def show_error( info):
    img = cv2.imread( '/home/pi/faceid/initerror.png')
    font = cv2.FONT_HERSHEY_DUPLEX
    imgzi = cv2.putText(img, info, (10, 100), font, 1, (255, 0, 0), 2,)

    wname='show'
    cv2.namedWindow(wname, 0);
    cv2.namedWindow(wname, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(wname, 0, 1) #(wname, cv2.WND_PROP_FULLSCREEN, cv2.cv.WINDOW_FULLSCREEN)
    cv2.imshow(wname, imgzi) 
    cv2.waitKey(0)

# main
if __name__ == '__main__':
    # load config
    try:
        data = json.load( open( '/home/pi/faceid/config.json'))
    except :
        show_error( 'Error:config file')
    print data
    # cloud sid, skey
    sid=data['sid']
    skey=data['skey']
    # pic path
    l_ck = data['logo']['checking']
    l_fa = data['logo']['failed']
    l_su = data['logo']['success']
    l_er = data['logo']['error']
    picpath=data['pic2check']
    su2halt=data['su2halt']

    # init Pin
    GPIO.setup(24, GPIO.OUT) # TrigPin
    GPIO.setup(23, GPIO.IN)  # EchoPin

    GPIO.setup(12, GPIO.OUT) # swith
    GPIO.output(12, 0)

    # start process
    q = multiprocessing.Queue() # pic:getpic f.0:wait f.1:checking f.2:failed f.3:success f.4:syserror other:text
    showvideo = multiprocessing.Process(target=showvideo, args=(l_ck, l_fa, l_su, l_er, picpath, q,))
    showvideo.start()

    # checking
    try:
        llength = 0
        while 1:
            # check distance
            dis = Distance_test(24,23)
            #q.put( str(25-int(dis)), block = False)
            if dis > 30 or 2 < (dis - llength):
                llength = dis
                time.sleep(0.3)
                continue
            # get pic
            q.put( 'pic', block = False)
            time.sleep( 0.3)
            q.put( 'f.1', block = False)
            # check pic
            rflag, info = checking(picpath, sid, skey)
            if rflag:
                # get result
                if checkresult(info):
                    q.put( 'f.3', block = False)
                    # right green powerlow
                    GPIO.output(12, 1)
                    time.sleep(5)
                    GPIO.output(12, 0)
                    if 1 == su2halt:
                        os.system('halt')
                    else:
                        q.put( 'f.0', block = False)
                else:
                    q.put( 'f.2', block = False)
                    # wrong red
                    time.sleep(2)
                    q.put( 'f.0', block = False)
            else:
                q.put( 'f.2', block = False)
                time.sleep(2)
                q.put( 'f.0', block = False)

    except Exception as e:
        print 'main:error '+str(e)
    else:
        pass
    finally:
        GPIO.cleanup()
