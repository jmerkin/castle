###############################################################################
# David Morgens
# 03/18/2016
###############################################################################
# Imports neccessary modules

from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LogNorm
import scipy.stats as st
import scipy.stats.mstats as ms
import csv
import sys
from collections import defaultdict
import argparse
from screenFun import *
import warnings
import math


###############################################################################    
# Version number

current_version = '1.0'


###############################################################################
# Parses input using argparse module

# Initiates input parser
parser = argparse.ArgumentParser(description='Visualizes replicate data')

# Non-optional arguments: The files containing results, as well as an output
parser.add_argument('res_file', help='File for untreated results', type=str)

# Optional arguments:
parser.add_argument('-hi', '--hist', action='store_false')
parser.add_argument('-of', '--override_file', action='store_true')
parser.add_argument('-x', '--x_axis', default='CasTLE Score')
parser.add_argument('-y', '--y_axis', default='CasTLE Gene Effect')
parser.add_argument('-f', '--file_type', default='png')

# Arguments for statistics
parser.add_argument('-p', '--pvalue', type=float)
parser.add_argument('-t', '--thresh', type=float)

# Arguments for labeling points
parser.add_argument('-n', '--names', help='List of genes to label', nargs='+', default=[])
parser.add_argument('-xl', '--xlim', nargs=2, type=float)
parser.add_argument('-yl', '--ylim', type=float)

# Arguments for changing columns
parser.add_argument('-r', '--rat_col', type=int)
parser.add_argument('-e', '--effect_col', type=int)
parser.add_argument('-pc', '--pval_col', type=int)
parser.add_argument('-g', '--gene_col', type=int, default=1)

#
parser.add_argument('-o', '--record', action='store_true')
parser.add_argument('-m', '--mouse', action='store_true')

# Saves all input to object args
args = parser.parse_args()


###############################################################################
# Checks arguments

file_name = args.res_file.split('.')[0]
file_out = file_name + '_volcano.' + args.file_type

try:
    with open(file_out, 'w') as out_open:
        pass

    os.remove(file_out)

except IOError:
    sys.exit('Cannot write to output file:\n' + file_out + '\n'
                + 'Use -of or --override_file to change')

if not os.path.isfile(args.res_file):
    sys.exit('Result files not found')


###############################################################################
# Finds count files

print('Retrieving records')

if not args.record:

    file_name = args.res_file.split('.')[0]
    rec_file = file_name + '_record.txt'

    try:

        with open(rec_file, 'r') as rec_open:
            rec_csv = csv.reader(rec_open, delimiter='\t')
            script, version = rec_csv.next()

            if version != current_version:
                sys.exit('Version number not current\n'
                            + 'Rerun analysis')

    except IOError:
        sys.exit('Record not found')

else:
    script = 'NONE'
    print('Warning: record overridden')


###############################################################################
#

if args.rat_col and args.effect_col:
    pass

elif script == 'analyzeCounts.py':

    if not args.rat_col:
        args.rat_col = 8

    if not args.effect_col:
        args.effect_col = 7

    if not args.pval_col:
        args.pval_col = 9

elif script == 'analyzeCombo.py':

    if not args.rat_col:
        args.rat_col = 14

    if not args.effect_col:
        args.effect_col = 13

    if not args.pval_col:
        args.pval_col = 15

else:
    sys.exit('Error: Result format not recognized')


###############################################################################
# Pulls in gene info, IDs, as well as GO terms

print('Retrieving gene information')

# Uses different genetic information depending whether a human or mouse screen
geneID2Name, geneID2Info, geneName2ID, geneEns2Name = retrieveInfo(mouse=args.mouse)

# Retrieves GO information
geneID2Comp, geneID2Proc, geneID2Fun = retrieveGO()


###############################################################################
# Parses results file

print('Parsing results')

gene2effect_rat = {}

with open(args.res_file, 'r') as res_open:

    res_csv = csv.reader(res_open, delimiter=',', lineterminator='\n')
    res_csv.next()

    for line in res_csv:
        gene = line[args.gene_col].upper()

        effect = float(line[args.effect_col])
        rat = float(line[args.rat_col])

        gene2effect_rat[gene] = (effect, rat)


###############################################################################
# Calculates FDRs

if args.pvalue:
    print('Warning: Feature does not exist, why would you think it did?')
    pass


###############################################################################
# Calculates threshold

thresh_genes = []


if args.thresh:

    for gene in gene2effect_rat:

        effect, rat = gene2effect_rat[gene]

        if rat > args.thresh:

            thresh_genes.append(gene)

    print('Warning: This one does though')


###############################################################################
# Finds labels

gene_labels = []

if args.names:
    for gene in args.names:

        geneID, name, entrez = retrieveIDs(gene, geneID2Name, geneName2ID, geneEns2Name)

        if gene.upper() in gene2effect_rat:
            gene_labels.append((gene, gene.upper()))

        elif geneID in gene2effect_rat:
            gene_labels.append((gene, geneID))

        elif name in gene2effect_rat:
            gene_labels.append((gene, name))

        elif entrez in gene2effect_rat:
            gene_labels.append((gene, entrez))

        else:
            print('Warning: ' + gene + ' not found')


###############################################################################
# Plots gene against gene using signed ratio statistic

print('Plotting figures')

x = []
y = []

for gene in gene2effect_rat:

#    if gene in thresh_genes:
#        continue

    effect, rat = gene2effect_rat[gene]

    x.append(effect)
    y.append(rat)

plt.figure(dpi=400)

if args.hist:
    plt.hist2d(x, y, 100, cmap=cm.jet, norm=LogNorm())

else:
    plt.plot(x, y, '.', color='0', alpha=0.25, markersize=10, markeredgewidth=0)

plt.xlabel(args.x_axis)
plt.ylabel(args.y_axis)

if args.ylim:
    maxy = args.ylim
    plt.ylim([0, maxy])

if args.xlim:
    minx, maxx = args.xlim
    plt.xlim([minx, maxx])

if args.names:
    for name, gene in gene_labels:
        effect, rat = gene2effect_rat[gene]
	plt.text(effect, rat, name)

if args.thresh:

    x_thresh, y_thresh = [], []

    for gene in thresh_genes:

        effect, rat = gene2effect_rat[gene]

        x_thresh.append(effect)
        y_thresh.append(rat)

    plt.plot(x_thresh, y_thresh, '.', color='red', markersize=10, markeredgewidth=0)

plt.savefig(file_out)
plt.close()

print('Finished')


###############################################################################
