/***Analyze Documents in BigQuery with Document AI***/
--Type of Document we are analyzing: Invoices from e-commerce compnay

/**Documentation**/
--Process Document - `https://cloud.google.com/bigquery/docs/process-document`
--BigQuery + Document AI (doucment analysis + generative AI use cases) - https://cloud.google.com/blog/products/data-analytics/add-gen-ai-to-your-apps-with-bigquery-and-document-ai-integration


/**BigQuery Cloud data Ware House Notes**/
--Store and analyze
  -- Structure Data
  -- Documents(unstructured data) like invoices, forms, contracts, and other documents
  -- Images, audio, video with Object Tables and Google Cloud Storage

/**Document AI**/
--Document AI on Vertex AI
  -- Takes unstructured data from your documents and transforms it into structured data making it easier to understand, analyze, and consume.
  -- BigQuery Machine Learning acts as a bridhe between BigQuery and Document AI. It lets you call upon Document AI`s powerful capabilities directly within BigQuery and using familiar SQL syntax.
  -- You simply invoke the ML.PROCESS_DOCUMENT function over an object table which points to your documents in Google Cloud Storage.
  -- The results are then returned directly to BigQuery Storage ready for you to analyze and compbine with your other business critical data.
  -- This integration with Document AI eliminates the need for custom coding to bring data into your data warehouse. Your documents can now flow effortlessly into your data warehouse securely, at scale, and using the SQL skills that your team already has.
--Analyzing complex documents shouldn't require deep AI experience. And BigQuery's integration with document AI lets you unlock documenty data with the power of SQL streamlining analysis like never before
--Once your document is extract you can perform a variety of additional analytics.
  --join document Entities with BigQuerry tables.
  --Augment with LLM-powered functions.
  --Generate embeddings + vector search and retieval-augmented generation use cases.


/**Walkthrough process**/
-- 1. Navigate to Document AI
-- 2. Search via the Processor Gallery
-- 3. Select the Invoice Parser and define a custom processor name for it and after select create
-- 4. You can find the available versions in the "Manage versiosns" tab, which will need in BigQuery
-- 5. Navigate to BigQuery and create a cloud resource connection this allows BigQuery to access the PDFs in cloud Storage and invoke jobs in Document AI
-- 6. To do so I will click on the +ADD button in the explorer panel of BQ, select connection to external data source as the source type, set the connection type to Vertex AI remote models, remote functions and BigLake (Cloud Resource), ang give the connection ID name doc_conn
-- 7. Ensure the region is set to Multi-region and then click on submit to add the connection
-- 8. Navigate to the cloud resource connection and you should see "Connection Info" and copy the service account ID.
-- 9. Open up IAM to give the service account permissions. Select Grant Access and copy and past the account ID in the New Principle dialogue box
-- 10. Assign 2 roles to the service account: Storage Object Viewer, Document AI Viewer
-- 11. Navigate back to big query to create the model


--CREATE MODEL (REMOTE MODEL)
CREATE OR REPLACE MODEL `<project>.<dataset>.<model_name>`
REMOTE WITH CONNECTION `<project_name>.<connection_name>` --connection string
OPTIONS (
  REMOTE_SERVICE_TYPE = `CLOUD_AI_DEVELOPMENT_V1`
  DOCUMENT_PROCESSOR = `<processor_location_uri>` --Retrieve from the DOCUMENT AI page for the invoice parser
);

--CREATE OBJECT TABLE --stores metadata of the files
CREATE OR REPLACE EXTERNAL TABLE `<project>.<dataset>.<object_table_name>`
WITH CONNECTION `<project_name>.<connection_name>` -- <project>.doc_conn - connection to vertex AI remote model 
OPTIONS(
  object_metadata = 'SIMPLE'
  uris = ['gs://<folder>/*']
)

--PARSE DOCUMENTS USING ML.PROCESS_DOCUMENT TVF
CREATE OR REPLACE TABLE `<project>.<dataset>.<parsed_table_name>`
AS
SELECT *
FROM ML.PROCESS_DOCUMENT(
  MODEL `<project>.<dataset>.<model_name>`,
  TABLE `<project>.<dataset>.<object_table_name>`
);

--LOOK AT STRUCTURED DATA FROM PARSED DOCUMENTS
SELECT
  invoice_date
  invoice_id,
  receiver_name,
  receiver_address,
  li. description,
  li.amount as price,
  li.quantity
FROM `<project>.<dataset>.<parsed_table_name>`, UNNSET ( line_item ) as li
ORDER BY invoice_date DESC;


/**BUSINESS VALUE EXAMPLES**/

--FIND THE BEST SELLING PRODUCT AMONGST THE PARSED DOCUMENTS
SELECT
  li.description,
  SUM(CAST(li.quantity AS INT)) AS total_quantity
FROM `<project>.<dataset>.<parsed_table_name>`, UNNEST( line_item ) as li
GROUP BY
  li.description
ORDER BY total_quantity DESC
LIMIT 3;
  

