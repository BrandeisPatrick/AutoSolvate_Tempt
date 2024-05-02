"""  
    fresp1 = open('resp1.in', 'w')
    fresp1.write( "Resp charges for organic molecule" + '\n')
    fresp1.write( " "   +  '\n')
    fresp1.write(" &cntrl" + '\n')
    fresp1.write(" " + '\n' )
    fresp1.write( " nmol = 1," + '\n')
    fresp1.write( " ihfree = 1," + '\n')
    fresp1.write( "ioutopt = 1," + '\n')
    fresp1.write( " " + '\n')
    fresp1.write( " &end" + '\n')
    fresp1.write( "    1.0" + '\n')
    fresp1.write(  "Resp charges for organic molecule" + '\n')
    print("%5d" %'0', end=' ', file=fresp1)
    print("%4d" %len(crds), file=fresp1)
    for i in range(len(crds)):
        elenum = elements_num[i]
        print("%5d" %elenum, end=' ', file=fresp1)
        print("%4s" %0, file=fresp1)
    fresp1.close()

    fresp2 = open('resp2.in','w')
    print("Resp charges for organic molecule", file=fresp2)
    print(" ", file=fresp2)
    print(" &cntrl", file=fresp2)
    print(" ", file=fresp2)
    print(" nmol = 1,", file=fresp2)
    print(" ihfree = 1,", file=fresp2)
    print(" ioutopt = 1,", file=fresp2)
    print(" iqopt = 2,", file=fresp2)
    print(" qwt = 0.00100,", file=fresp2)
    print(" ", file=fresp2)
    print(" &end", file=fresp2)
    print("    1.0", file=fresp2)
    print("Resp charges for organic molecule", file=fresp2)
    print("%5d" %0, end=' ', file=fresp2)
    print("%4d" %len(len(crds)), file=fresp2)
    for i in atids:
        print("%5d" %iddict[i][1], end=' ', file=fresp2)
        print("%4s" %iddict[i][2], file=fresp2)
    fresp2.close()    
"""