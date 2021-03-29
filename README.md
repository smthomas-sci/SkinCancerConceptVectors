<center>
 
 # [In Review] Characterization of Tissue Types in Basal Cell Carcinoma Images via Generative Modelling and Concept Vectors
 
 </center>

<center>


[**Print Print**](https://smthomas-sci.github.io/Preprints/SkinCancerConceptVectors/)


</center>

Authors:
- [Simon M. Thomas](https://orcid.org/0000-0003-4609-2732) **a, b**,
- [James G. Lefevre](https://orcid.org/0000-0002-5945-9575) **a**
- Glenn Baxter **b**
- [Nicholas A. Hamilton](https://orcid.org/000-0003-0331-3427) **a**

**a** - Institute for Molecular Bioscience, The University of Queensland, St Lucia, Australia

**b** - MyLab Pty. Ltd., Salisbury, Australia

### Abstract
The promise of machine learning methods to act as decision support systems for
pathologists continues to grow. However, central to their successful adoption
must be interpretable implementations so that people can trust and learn from
them effectively. Generative modeling, most notable in the form of adversarial
generative models, is a naturally interpretable technique because the quality of
the model is explicit from the quality of images it generates. Such a model can
be further assessed by exploring its latent space, using human-meaningful
concepts by defining concept vectors. Motivated by these ideas, we apply for the
first time generative methods to histological images of basal cell carcinoma
(BCC). By simultaneously learning to generate and encode realistic image
patches, we extract feature rich latent vectors that correspond to various
tissue morphologies, namely BCC, epidermis, keratin, papillary dermis and
inflammation. We show that a logistic regression model trained on these latent
vectors can achieve high classification accuracies across 6 binary tasks
(86-98%). Further, by projecting the latent vectors onto learned concept vectors
we can generate a score for the absence or degree of presence for a given
concept, providing semantically accurate “conceptual summaries” of the various
tissues types within a patch. This can be extended to generate multi-dimensional
heat maps for whole-image specimens, which characterizes the tissue in a similar
way to a pathologist. We additionally find that accurate concept vectors can be
defined using a small labeled dataset.



