import streamlit as st
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from st_chat_message import message



msg1 = """
Hi!, I pass butter and display **markdown**.

```python
import streamlit as st
from st_chat_message import message

message("Hi, there!")
message("Hello *bot*!", is_user=True)  # aligns the message to the right 
```
"""

msg2 = r"""
I also can display $\LaTeX$: 

$$
\begin{aligned}
\frac{d}{dx} \left( \int_{a}^{x} f(u)\,du\right) &= f(x) \
\frac{d}{dx} \left( \int_{x}^{b} f(u)\,du\right) &= -f(x) \
\end{aligned}
$$

and tabular data.

### Maxwell's equations

| Equation | Name |
| --- | --- |
| $\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}$ | Gauss's law |
| $\nabla \cdot \mathbf{B} = 0$ | Gauss's law for magnetism |
| $\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}$ | Faraday's law of induction |
| $\nabla \times \mathbf{B} = \mu_0 \mathbf{J} + \mu_0 \varepsilon_0 \frac{\partial \mathbf{E}}{\partial t}$ | Ampère's circuital law |

"""

if "msgs" not in st.session_state:
    st.session_state.msgs = [{
        "content": "Hi, what is your purpose?",
        "is_user": True,
    }, {
        "content": msg1,
        "is_user": False,
    }, {
        "content": "That's great!, What else can you do?",
        "is_user": True,
    }, {
        "content": msg2,
        "is_user": False,
    }]


for idx, msg in enumerate(st.session_state.msgs):
    message(msg["content"], is_user=msg["is_user"], key=f"message_{idx}")

