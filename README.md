# Heading 1 (For your main title)

## Heading 2 (For your sections like "How to Run")

* A bullet point
* Item 1
* Item 2
    * Nested Item 2a
    * Nested Item 2b
    * sadsa
1.  First item
2.  Second item
3.  Third item
    1.  Nested item 3a
    1.  asdsa
    2.  
**This text is bold**

`This is an inline code block`

```bash
python -m app.main
```


# NavigateTheWeb
The initial project should be able to navigate a website, extract information from it and also download some documents as pdfs or archives. The archives will contain pdfs or word documents. Some of the PDFs might be scanned so non searchable and these will need to be turned into searchable. The end goal is to have a database with all the information from these documents so when a user needs to find some information about a client, they can search keywords and find what documents have that information. So the system will first navigate a website, extract all the information and documents, remember what documents were already extracted as this process can happen multiple times. process the documents as follows: 

1. if document is searchable PDF, save that information in the db so it can be searched for later

2. if document is not a searchable pdf, turn it into a searchable pdf and save that information in the db so it can be searched for later. Keep the searchable document into root folder of the client and move the original pds into a folder called 'original' that will also be in the root folder of the client

3. if document is archive, extract the archive. in the extracted documents, if there are other archives, extract them as well untill no other archives are found and only pdf and doc or docs files are 

4. folder structure of the documents will be as follows: 

clients
  --ClientNo
       --original
         doc1.pdf
       doc1.pdf
       doc2.docs

so all clients will be in the 'clients' folder and then any new discovered clients will have their own folder named with its number. all the documents that are searchable will be in the root folder and all the original files that have been processed will be moved into 'original' folder having the same name

5. when the extraction process is triggered, only extract information and documents starting from the day before up until the last extraction day. the process will only deal with full days so that we can avoid complex scenarios. so if the last extraction was made on the 21.09.2025 and we are triggering another one on the 02.10.2025, only information and documents from the 22.09.2025 to 01.10.2025 will be extracted. 
