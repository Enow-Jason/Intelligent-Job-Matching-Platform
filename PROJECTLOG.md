# Project Log

Please regularly update this file to record your project progress. You should be updating the project log _at least_ once a fortnight.

## Week 1 [w/c 6 October 2025]

- Confirmed project topic and refined the initial problem statement around AI-powered job matching.
- Began background reading on online job platforms and their limitations.
- Identified the main issue of keyword-based matching failing to capture semantic similarity.
- Started thinking about possible user groups and the overall system scope.

## Week 2 [w/c 13 October 2025]

- Continued literature review on semantic job matching, NLP in recruitment, and recommender systems.
- Reviewed existing platforms such as LinkedIn, Indeed, and Glassdoor.
- Identified key problems affecting graduates, including cold-start issues and over-reliance on exact keywords.
- Started drafting aims and objectives for the project.

## Week 3 [w/c 20 October 2025]

- Refined project aims, objectives, and expected deliverables.
- Decided to use transformer-based NLP rather than attempting to build a model from scratch.
- Began high-level architecture planning.
- Considered using React for the frontend, Spring Boot for the backend, and Python for AI functionality.

## Week 4 [w/c 27 October 2025]

- Produced initial architecture ideas for the system.
- Decided to separate the AI functionality from the backend using a microservice approach.
- Compared possible database choices and the overall technology stack.
- Continued reading on BERT, Sentence Transformers, and semantic similarity methods.

## Week 5 [w/c 3 November 2025]

- Searched for suitable datasets for resumes and job descriptions.
- Reviewed available Kaggle datasets for quality, structure, and usefulness.
- Chose to work with synthetic data to avoid privacy issues.
- Began planning how the raw data would be cleaned and transformed.

## Week 6 [w/c 10 November 2025]

- Finalised selection of the two main datasets:
  - Job Descriptions 2025 – Tech & Non-Tech Roles
  - Resume and Job Description
- Inspected the structure of both datasets.
- Identified important columns such as title, skills, experience, and target job description.
- Noted that the data was mostly clean but would still require normalisation.

## Week 7 [w/c 17 November 2025]

- Started writing the interim report based on the background research and architecture decisions.
- Documented aims, objectives, literature review, functional requirements, and non-functional requirements.
- Recorded anticipated challenges including data quality, model choice, and system integration.

## Week 8 [w/c 24 November 2025]

- Completed and refined the interim report.
- Reviewed the original project timeline and recognised that the AI matching component would be the core technical focus.
- Decided to prioritise model quality and evaluation before broader system features.

## Week 9 [w/c 1 December 2025]

- Set up the project repository and GitLab issue board structure.
- Created issue tracking categories for data, AI, backend, frontend, and documentation.
- Began planning work in smaller, manageable tasks.
- Confirmed that Jupyter notebooks would be used for experimentation and preprocessing.

## Week 10 [w/c 8 December 2025]

- Began practical data work in Jupyter.
- Loaded both datasets into pandas and inspected shapes, columns, and sample rows.
- Checked missing values and data types.
- Confirmed that the datasets were suitable for preprocessing and model development.

## Week 11 [w/c 15 December 2025]

- Carried out initial exploratory analysis focused on project needs rather than full EDA.
- Investigated skill formats, title consistency, and experience field structure.
- Noted that `YearsOfExperience` in the jobs dataset was stored as text ranges rather than numeric values.
- Confirmed that skill lists would need parsing and normalisation.

## Week 12 [w/c 22 December 2025]

- Built canonical preprocessing logic for both datasets.
- Created cleaned tables for jobs and resumes.
- Generated structured fields such as:
  - `job_text`
  - `resume_text`
  - `job_skills_list`
  - `resume_skills_list`
- Saved processed outputs locally for reuse.

## Week 13 [w/c 29 December 2025]

- Validated preprocessing outputs.
- Confirmed that no empty `job_text` or `resume_text` fields remained after cleaning.
- Built a unified skills vocabulary from both datasets.
- Prepared the data for embedding generation.

## Week 14 [w/c 5 January 2026]

- Implemented the baseline semantic embedding pipeline.
- Used `sentence-transformers/all-MiniLM-L6-v2` to generate embeddings for resumes and jobs.
- Saved embeddings for efficient reuse.
- Verified embedding dimensions and successful encoding.

## Week 15 [w/c 12 January 2026]

- Built baseline matching functions using cosine similarity.
- Implemented:
  - resume → top job matches
  - job → top candidate matches
- Tested retrieval outputs manually to check whether the recommendations were broadly sensible.

## Week 16 [w/c 19 January 2026]

- Added initial skill-gap analysis.
- Compared resume skills against job skills to produce matched and missing skill lists.
- Extended outputs beyond a single match score to improve explainability.
- Began considering whether strict exact skill matching was too limited.

## Week 17 [w/c 26 January 2026]

- Observed that semantic matching alone could return unrealistic senior roles for freshers.
- Designed a soft experience-aware reranking approach instead of hard filtering.
- Parsed job experience ranges and mapped them into minimum experience requirements.
- Implemented an experience penalty function.

## Week 18 [w/c 2 February 2026]

- Integrated the experience-aware reranking logic into the matching pipeline.
- Tested fresher examples and confirmed that trainee/junior roles moved higher in the rankings.
- Improved practical realism of results without excluding potential stretch opportunities.

## Week 19 [w/c 9 February 2026]

- Refined the skill-gap explanation output.
- Ranked missing skills by frequency to make them more actionable.
- Limited missing-skill output to top-N items for readability.
- Continued manually validating match explanations.

## Week 20 [w/c 16 February 2026]

- Built the quantitative evaluation notebook.
- Defined proxy ground truth:
  - current job title for experienced users
  - inferred target role for freshers
- Implemented evaluation metrics:
  - Precision@K
  - MRR
  - Top-1 Accuracy

## Week 21 [w/c 23 February 2026]

- Ran baseline evaluation on the experienced subset.
- Analysed retrieval quality and documented initial performance.
- Noted that the baseline semantic model already performed reasonably well without supervised fine-tuning.
- Began comparing enhanced ranking variants against the baseline.

## Week 22 [w/c 2 March 2026]

- At the start of the week, began contemplating a refinement of the project scope to focus more strongly on the job seeker rather than supporting both job seekers and employers equally.
- Reflected on the fact that the strongest technical contribution so far was the resume-to-job recommendation pipeline.
- Considered reframing the system as an AI-assisted job discovery and career guidance platform for job seekers.
- Performed a small weight sweep for the enhanced reranking model.
- Found that the best-performing configuration was:
  - 0.8 semantic similarity
  - 0.2 experience-adjusted semantic similarity
  - 0.0 skill-overlap boost
- Concluded that skill boosting did not improve title-based ranking accuracy.
- Retained skill matching for explainability only.

## Week 23 [w/c 9 March 2026]

- Evaluated freshers separately using inferred ground-truth roles from target job descriptions.
- Confirmed that the tuned enhanced model improved top-K retrieval for freshers, even where Top-1 remained noisy.
- Finalised the model selection and evaluation summary.
- Packaged the AI logic into a FastAPI microservice.
- Built and tested endpoints for:
  - `/match/jobs-for-resume`
  - `/match/resumes-for-job`
- Began improving the skill explanation layer using stronger skill normalisation and semantic skill matching.