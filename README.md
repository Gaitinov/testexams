# Testing System (main.pyw)

## Description

This application is designed for conducting tests using a graphical interface based on customtkinter. Questions are loaded from `.docx` files, and test results can be exported.

## Question File Format (.docx)

The file must be in Microsoft Word (`.docx`) format and contain questions and answer options using special tags:

* `<question>` — start of a new question
* `<variant>` — answer option

### Example:

```
<question> Which programming language is used for this application?
<variant> Python
<variant> Java
<variant> C++
<variant> JavaScript
<question> Which module is used to work with .docx?
<variant> python-docx
<variant> pandas
<variant> openpyxl
<variant> docutils
```

The correct answer should be the first one after `<question>` (or defined in the application logic).

## Images

The application supports displaying images in questions.

**How to add an image:**

1. Open the `.docx` file with questions in Microsoft Word.
2. Add a `<question>` tag with the question text.
3. *After* the paragraph with the `<question>` tag, but *before* any `<variant>`, insert an image.

**Important:**

* The image must be *embedded* in the `.docx` file, not linked.
* Supported image formats: PNG, JPG, JPEG.

## Features

* Load questions from `.docx`
* Display images in questions
* Shuffle questions and answers
* Time and question count limits
* Export incorrect answers
* Modern interface (customtkinter)
