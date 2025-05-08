from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """
Voici un email :

"{email}"

Analyse le contenu de cet email et indique le domaine principal auquel il appartient parmi cette liste :
{domain_list}

Donne uniquement le nom du domaine, sans explication.

Domaine :"""


def chat(mail_content, user_domains):
    user_domains_prompt = "\n- " + "\n- ".join(user_domains)

    template = f"""
Voici un email :

"{{email}}"

Analyse le contenu de cet email et indique le domaine principal comme les domaines suivants :
{user_domains_prompt}

Donne uniquement le nom du domaine, sans explication.

Domaine :"""

    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model="gemma2:2b", max_tokens=10)
    chain = prompt | model
    result = chain.invoke({"email": mail_content})
    return result


#######  automove :
def match_email_with_prompt(email_content, user_prompt):
    template = """
Voici un email :

"{email}"

Règle utilisateur :
"{user_prompt}"

Réponds uniquement par OUI si l'email correspond à la règle, sinon réponds NON.
Réponse :
"""
    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model="gemma2:2b", max_tokens=5)
    chain = prompt | model
    result = chain.invoke({"email": email_content, "user_prompt": user_prompt})
    return result.strip().lower() == "oui"

## reply :
def response(mailcontent, user_prompt, theme):
    template = """
    Email reçu :

    "{email}"

    Thème attendu : "{theme}"

    Objectif : rédiger une réponse formelle, courte mais complète (environ 4 phrases), adaptée à l'email **uniquement si** le thème correspond.

    Instructions pour écrire la réponse :
    "{user_prompt}"

    Si le thème ne correspond pas, réponds uniquement par : "Hors sujet".

    Réponse :
    """
    prompt_template = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model="mistral", max_tokens=200)
    chain = prompt_template | model
    result = chain.invoke({
        "email": mailcontent,
        "user_prompt": user_prompt,
        "theme": theme
    })
    return result.strip()