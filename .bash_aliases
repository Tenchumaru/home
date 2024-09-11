cd_() {
	"cd" "$@" && ls --color=auto -F
}
gds_() {
	[ "$1" ] || return
	for c in $(git log --name-status | grep -m $1 '^commit ' | sed 's/commit //'); do
		echo commit $c
		(echo; git log --name-status) | sed -e "1,/$c/d" -e '/^commit /q' | grep -v '^commit '
		git diff $c^ $c
		echo
	done
}
glgd_() {
	git log --name-status | sed /$1/q
	echo
	git diff $1
}
gr_() {
	T=$(mktemp --directory)
	grep '/$' .gitignore | sed -e 's/\[.\(.\)\]/\1/g' -e 's/\///g' | sed 's/\(.*\)/\/\\\/\1\\\/\/Id/' | sed 's/\*/.*/g' > $T/t
	echo grep \\ > $T/u
	for arg in "$@"; do
		if echo $arg | grep -F "'" > /dev/null; then
			echo '"'$arg'" \' >> $T/u
		else
			echo "'"$arg"' \\" >> $T/u
		fi
	done
	find . -type f | sed -e 's/^/ "/' -e 's/$/" \\/' | grep -Fv /.git/ >> $T/u
	sed -f $T/t $T/u > $T/v
	bash $T/v
	rm -r $T
}
pd_() {
	pushd "$@" && ls --color=auto -F
}
pp_() {
	popd "$@" && ls --color=auto -F
}
find_git_() {
	D=.
	while ! [ -d "$D/.git" ]; do
		D=$(readlink -f "$D/..")
		if [ "$D" = "/" ]; then
			D=
			return
		fi
	done
}
get_branch_() {
	B=
	find_git_
	[ "$D" ] || return
	B=$(git branch 2> /dev/null | grep -F "*" | sed -e s/..// -e 's/(.* //' -e 's/)//')
}
select_main_branch_() {
	for B in dev main master; do
		if git switch $B 2> /dev/null; then
			return
		fi
	done
	B=
}
rall_() {
	select_main_branch_
	[ "$B" ] || return
	for branch in $(git branch | grep -v " $B\$"); do
		echo "$branch" | grep -Fiq release && continue
		git switch "$branch" || return
		git rebase $B || return
	done
	git switch $B
}
gaca_() {
	find_git_
	[ "$D" ] || return
	git add "$D"
	git commit --amend
}
wip_() {
	find_git_
	[ "$D" ] || return
	git add "$D" && git commit -m WIP
}
ephemeral_() {
	get_branch_
	[ "$B" = "ephemeral" -o -z "$B" ] && return
	git checkout -b ephemeral && git add "$D" && git commit -m WIP && git switch $B
}
rephemeral_() {
	B=$(git branch 2> /dev/null | grep -F "*" | sed -e s/..// -e 's/(.* //' -e 's/)//')
	[ "$B" = "ephemeral" ] && return
	git checkout ephemeral &&
		git rebase $B &&
		git switch $B &&
		git merge --ff-only ephemeral &&
		git branch -d ephemeral &&
		git reset HEAD^
}
vc_() {
	vi $(git status -s | grep -E '(U.)|(.U)' | cut -c 4-)
}

alias b='cd ..'
alias cd=cd_
alias ephemeral=ephemeral_
alias gaca=gaca_
alias gbs='git bisect start && git bisect bad && git bisect good'
alias gca='git commit --amend'
alias gcm='git commit -m'
alias gd='git diff'
alias gds=gds_
alias gh='history | grep'
alias gl='git log --name-status'
alias glgd=glgd_
alias gmc='git mergetool && git clean -f'
alias gr=gr_
alias grc='git rebase --continue'
alias grep='grep --color=auto'
alias gri='git rebase -i'
alias gs='git status -s'
alias gsu='git submodule update'
alias gx='git checkout'
alias h=history
alias j=jobs
alias la='ls -A'
alias lal='la -l'
alias ll='ls -l'
alias ls='ls --color=auto -F'
alias md=mkdir
alias pbcopy='xclip -i -selection clipboard'
alias pd=pd_
alias pp=pp_
alias rall=rall_
alias rd=rmdir
alias rephemeral=rephemeral_
alias tm='tmux attach || tmux new'
alias vc=vc_
alias wip=wip_
