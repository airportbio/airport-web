import glob
import json
from os import path

server_names = {"PANTHER": "ftp.pantherdb.org",
 "miRBase": "mirbase.org",
 "Ensembl Genome Browser": "ftp.ensembl.org",
 "Rat Genome Database": "ftp.rgd.mcw.edu",
 "Genomicus": "ftp.biologie.ens.fr",
 "Human Microbiome Project": "public-ftp.hmpdacc.org",
 "Protein Information Resource": "ftp.pir.georgetown.edu",
 "The Arabidopsis Information Resource": "ftp.arabidopsis.org/home",
 "AAindex": "ftp.genome.jp",
 "O-GLYCBASE": "ftp.cbs.dtu.dk",
 "Xenbase": "ftp.xenbase.org",
 "Pasteur Insitute": "ftp.pasteur.fr",
 "Uniport": "ftp.uniprot.org",
 "Flybase": "ftp.flybase.net",
 "NECTAR": "ftp.nectarmutation.org",
 "Global Proteome Machine and Database": "ftp.thegpm.org",
 "REBASE": "ftp.neb.com",
 "UCSC Genome Browser": "hgdownload.cse.ucsc.edu",
 "PairsDB": "nic.funet.fi",
 "Molecular INTeraction database": "mint.bio.uniroma2.it",
 "Gene Expression Omnibus": "ftp.ncbi.nlm.nih.gov",
 "One Thousand Genomes Project": "ftp.ncbi.nlm.nih.gov/1000genomes",
 "dbGaP": "ftp.ncbi.nlm.nih.gov/dbgap",
 "GenBank": "ftp.ncbi.nlm.nih.gov/genbank",
 "Epigenomics Database": "ftp.ncbi.nlm.nih.gov/epigenomics",
 "Sequence Read Archive": "ftp.ncbi.nlm.nih.gov",
 "RefSeq": "ftp.ncbi.nlm.nih.gov/refseq/",
 "Entrez": "ftp.ncbi.nlm.nih.gov/entrez",
 "HapMap": "ftp.ncbi.nlm.nih.gov/HapMap"}


def create_meta(d, name):
    s_name = name.replace('.json', '')
    root = path.basename(server_names[s_name])
    if root == '':
        root = '/'
    new = {}
    for p, files in d.items():
        l = [name for name in files if 'readme' in name.lower()]
        if l:
            new[p] = l
    print(len(new))
    final = {}
    for p, files in new.items():
        l = []
        t = path.dirname(p)
        while t not in {'/','', '/.', root}:
            try:
                l.extend([path.join(t, f) for f in new[t]])
            except KeyError:
                pass
            t = path.dirname(t)
            # print(t)
        # print(p)
        final[p] = l + [path.join(p, f) for f in files]

    return final

for name in glob.glob('*.json'):
    print(name)
    with open(name) as f:
        d = json.load(f)
    with open(path.join('meta/', name), 'w') as f:
        json.dump(create_meta(d, name), f, indent=4)

