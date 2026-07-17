char szBuffer[256];
char szNum[8];
int i;
int pos[8];
int lastPos[8];
int changed;

// After a restart the physical RTS shades have NOT moved -- only the program
// state was lost. RTS is one-way (no position feedback), so re-commanding
// every shade on startup causes each estimated move to drift a little; several
// restarts in a row push shades far off target (e.g. fully closed instead of
// 15%). So we seed the baseline from the current TPos inputs WITHOUT sending,
// and only publish genuine changes afterwards.
sleep(3000);                          // let TPos inputs settle after restart
for (i = 0; i < 8; i++) {
    lastPos[i] = 100 - (int)getinput(i);
}

while(1) {
    if (getinputevent()) {
        changed = 0;
        for (i = 0; i < 8; i++) {
            pos[i] = 100 - (int)getinput(i);
        }

        strcpy(szBuffer, "{\"cmd\":\"Position\",\"shades\":{");
        for (i = 0; i < 8; i++) {
            if (pos[i] != lastPos[i]) {
                if (changed > 0) strcat(szBuffer, ",");
                sprintf(szNum, "\"%d\":%d", i+1, pos[i]);
                strcat(szBuffer, szNum);
                lastPos[i] = pos[i];
                changed++;
            }
        }
        strcat(szBuffer, "}}");

        if (changed > 0) {
            setoutputtext(0, szBuffer);
        }
    }
    sleep(100);
}
