char szBuffer[256];
char szNum[8];
int i;
int pos[8];
int lastPos[8];
int changed;

for (i = 0; i < 8; i++) {
    lastPos[i] = -1;
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
