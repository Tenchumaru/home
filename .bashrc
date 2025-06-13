# https://docs.github.com/en/authentication/connecting-to-github-with-ssh/working-with-ssh-key-passphrases#auto-launching-ssh-agent-on-git-for-windows
env=~/.ssh/agent.env
agent_load_env () { test -f "$env" && . "$env" >| /dev/null ; }
agent_start () {
    (umask 077; ssh-agent >| "$env")
    . "$env" >| /dev/null ; }
agent_load_env
# agent_run_state: 0=agent running w/ key; 1=agent w/o key; 2= agent not running
agent_run_state=$(ssh-add -l >| /dev/null 2>&1; echo $?)
if [ ! "$SSH_AUTH_SOCK" ] || [ $agent_run_state = 2 ]; then
    agent_start
    ssh-add
elif [ "$SSH_AUTH_SOCK" ] && [ $agent_run_state = 1 ]; then
    ssh-add
fi
unset env

# If not running interactively, do no more.
[ -z "$PS1" ] && return

# Remove duplicate lines and lines starting with space from the history.
HISTCONTROL=ignoreboth
HISTFILESIZE=2000
HISTSIZE=2000

# Append to the history file, don't overwrite it.
shopt -s histappend

# Also save each command right after it has run.
# https://superuser.com/questions/211966/how-do-i-keep-my-bash-history-across-sessions
# https://linuxcommando.blogspot.com/2007/11/keeping-command-history-across-multiple.html
PROMPT_COMMAND='history -a'

# Check the window size after each command and, if necessary, update the values
# of LINES and COLUMNS.
shopt -s checkwinsize

# Set alias definitions.
if [ -f ~/.bash_aliases ]; then
	. ~/.bash_aliases
fi

# http://unix.stackexchange.com/questions/148/colorizing-your-terminal-and-shell-environment
export COLOR_OFF='\e[0m'
export COLOR_BLACK='\e[0;30m'
export COLOR_RED='\e[0;31m'
export COLOR_GREEN='\e[0;32m'
export COLOR_BROWN='\e[0;33m'
export COLOR_BLUE='\e[0;34m'
export COLOR_PURPLE='\e[0;35m'
export COLOR_CYAN='\e[0;36m'
export COLOR_LIGHT_GREY='\e[0;37m'
export COLOR_GREY='\e[1;30m'
export COLOR_LIGHT_RED='\e[1;31m'
export COLOR_LIGHT_GREEN='\e[1;32m'
export COLOR_YELLOW='\e[1;33m'
export COLOR_LIGHT_BLUE='\e[1;34m'
export COLOR_LIGHT_PURPLE='\e[1;35m'
export COLOR_LIGHT_CYAN='\e[1;36m'
export COLOR_WHITE='\e[1;37m'
