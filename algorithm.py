import string

def getNext(charlist, increment, ID, current):
    count = 0
    nxt = ""
    if(current == ""):                                                                     
        return charlist[increment-1+ID]                                                  
    else:
        for i in range(len(current)-1, -1, -1):              
            ind = charlist.index(current[i])
            if count == 0:
                if ind+increment >= len(charlist):
                    nxt = charlist[(ind+increment)%len(charlist)] + nxt
                    increment = 1
                else:
                    count = 1
                    nxt = charlist[ind+increment] + nxt
                    increment = 1
            else:
                nxt = current[i] + nxt
        if count == 0:
            nxt = charlist[0] + nxt
        return nxt                         
