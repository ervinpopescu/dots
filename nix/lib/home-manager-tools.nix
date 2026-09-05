{
  homeManagerPackage,
  pkgs,
}:
let
  renameNoReplace = pkgs.stdenv.mkDerivation {
    pname = "hm-rename-no-replace";
    version = "1";
    dontUnpack = true;

    buildPhase = ''
      $CC -std=c11 -Wall -Wextra -Werror \
        ${../scripts/hm-rename-no-replace.c} -o hm-rename-no-replace
    '';

    installPhase = ''
      install -D -m 0755 hm-rename-no-replace \
        "$out/bin/hm-rename-no-replace"
    '';
  };

  checkCollisions = pkgs.writeShellApplication {
    name = "hm-check-collisions";
    runtimeInputs = [ pkgs.coreutils ];
    text = builtins.readFile ../scripts/hm-check-collisions.sh;
  };

  backupCollision = pkgs.writeShellApplication {
    name = "hm-backup-collision";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.flock
    ];
    text = ''
      export HM_RENAME_NOREPLACE_BIN="''${HM_RENAME_NOREPLACE_BIN:-${renameNoReplace}/bin/hm-rename-no-replace}"
      ${builtins.readFile ../scripts/hm-backup-collision.sh}
    '';
  };

  backupCollisionForActivation = pkgs.writeShellApplication {
    name = "hm-backup-collision-for-activation";
    runtimeInputs = [ backupCollision ];
    text = ''
      export HM_LINK_ACTIVATION_ID="''${HM_LINK_ACTIVATION_ID:-hm-link-$$-$RANDOM-$RANDOM}"
      if hm-backup-collision "$@"; then
        exit 0
      else
        status=$?
      fi
      kill -KILL "$PPID"
      exit "$status"
    '';
  };

  safeLink = pkgs.writeShellApplication {
    name = "ln";
    runtimeInputs = [
      backupCollisionForActivation
      pkgs.coreutils
    ];
    text = ''
      export HM_LINK_ACTIVATION_ID="''${HM_LINK_ACTIVATION_ID:-hm-link-$$-$RANDOM-$RANDOM}"
      export HM_BACKUP_COMMAND="''${HM_BACKUP_COMMAND:-${backupCollisionForActivation}/bin/hm-backup-collision-for-activation}"
      export HM_RENAME_NOREPLACE_BIN="''${HM_RENAME_NOREPLACE_BIN:-${renameNoReplace}/bin/hm-rename-no-replace}"
      export HM_REAL_LN="''${HM_REAL_LN:-${pkgs.coreutils}/bin/ln}"
      export HM_REAL_RM="''${HM_REAL_RM:-${pkgs.coreutils}/bin/rm}"
      export HM_STORE_DIR="''${HM_STORE_DIR:-${builtins.storeDir}}"
      ${builtins.readFile ../scripts/hm-link-no-clobber.sh}
    '';
  };

  safeRemove = pkgs.writeShellApplication {
    name = "rm";
    runtimeInputs = [
      backupCollisionForActivation
      pkgs.coreutils
    ];
    text = ''
      export HM_BACKUP_COMMAND="''${HM_BACKUP_COMMAND:-${backupCollisionForActivation}/bin/hm-backup-collision-for-activation}"
      export HM_REAL_RM="''${HM_REAL_RM:-${pkgs.coreutils}/bin/rm}"
      export HM_RENAME_NOREPLACE_BIN="''${HM_RENAME_NOREPLACE_BIN:-${renameNoReplace}/bin/hm-rename-no-replace}"
      export HM_STORE_DIR="''${HM_STORE_DIR:-${builtins.storeDir}}"
      ${builtins.readFile ../scripts/hm-rm-no-clobber.sh}
    '';
  };

  restoreCollisions = pkgs.writeShellApplication {
    name = "hm-restore-backups";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.findutils
      pkgs.flock
    ];
    text = ''
      export HM_RENAME_NOREPLACE_BIN="''${HM_RENAME_NOREPLACE_BIN:-${renameNoReplace}/bin/hm-rename-no-replace}"
      ${builtins.readFile ../scripts/hm-restore-collisions.sh}
    '';
  };

  switchCommand = pkgs.writeShellApplication {
    name = "hm-switch";
    runtimeInputs = [
      homeManagerPackage
      pkgs.coreutils
    ];
    text = ''
      export HOME_MANAGER_BIN="''${HOME_MANAGER_BIN:-${homeManagerPackage}/bin/home-manager}"
      export HM_BACKUP_COMMAND="''${HM_BACKUP_COMMAND:-${backupCollisionForActivation}/bin/hm-backup-collision-for-activation}"
      export HM_RESTORE_COMMAND="''${HM_RESTORE_COMMAND:-${restoreCollisions}/bin/hm-restore-backups}"
      ${builtins.readFile ../scripts/hm-switch.sh}
    '';
  };

  darwinSwitchCommand = pkgs.writeShellApplication {
    name = "darwin-switch";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.nix
      restoreCollisions
    ];
    text = ''
      export DARWIN_REBUILD_BIN="''${DARWIN_REBUILD_BIN:-darwin-rebuild}"
      export HM_RESTORE_COMMAND="''${HM_RESTORE_COMMAND:-${restoreCollisions}/bin/hm-restore-backups}"
      export NIX_STORE_BIN="''${NIX_STORE_BIN:-${pkgs.nix}/bin/nix-store}"
      export SUDO_BIN="''${SUDO_BIN:-/usr/bin/sudo}"
      ${builtins.readFile ../scripts/darwin-switch.sh}
    '';
  };

  preflight = pkgs.writeShellApplication {
    name = "hm-preflight";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.diffutils
      pkgs.findutils
      pkgs.gnugrep
      pkgs.nix
    ];
    text = ''
      export NIX_BIN="''${NIX_BIN:-${pkgs.nix}/bin/nix}"
      export HM_STORE_DIR="''${HM_STORE_DIR:-${builtins.storeDir}}"
      ${builtins.readFile ../scripts/hm-preflight.sh}
    '';
  };

  test = pkgs.runCommand "home-manager-backup-restore-test" { } ''
    export HOME="$TMPDIR/home"
    export USER="test-user"
    export XDG_STATE_HOME="$TMPDIR/state"
    export HM_BACKUP_ID="test-session"
    export HM_BACKUP_SESSION="$XDG_STATE_HOME/home-manager/collision-backups/$HM_BACKUP_ID"

    mkdir -p "$HOME/config with spaces" "$HM_BACKUP_SESSION"
    printf 'original\n' > "$HOME/config with spaces/file"
    ${backupCollision}/bin/hm-backup-collision "$HOME/config with spaces/file"
    test ! -e "$HOME/config with spaces/file"
    test -e "$HOME/config with spaces/file.$HM_BACKUP_ID"
    printf 'new managed source\n' > "$TMPDIR/guard-source"
    ln -s /nix/store/racer-home-manager-files/file "$HOME/config with spaces/file"
    if ${safeLink}/bin/ln -Tsf "$TMPDIR/guard-source" "$HOME/config with spaces/file"; then
      echo "safe linker overwrote a target recreated after backup" >&2
      exit 1
    fi
    test "$(readlink "$HOME/config with spaces/file")" = \
      /nix/store/racer-home-manager-files/file
    rm "$HOME/config with spaces/file"

    printf 'guarded original\n' > "$HOME/config with spaces/guarded-race"
    HM_LINK_ACTIVATION_ID=guarded-race \
      ${backupCollision}/bin/hm-backup-collision \
      "$HOME/config with spaces/guarded-race"
    guarded_checkpoints="$TMPDIR/guarded-checkpoints"
    mkdir -p "$guarded_checkpoints"
    HM_LINK_ACTIVATION_ID=guarded-race \
      HM_LINK_TEST_CHECKPOINT_DIR="$guarded_checkpoints" \
      ${safeLink}/bin/ln -Tsf "$TMPDIR/guard-source" \
      "$HOME/config with spaces/guarded-race" &
    guarded_pid=$!
    for attempt in $(seq 1 1000); do
      [[ -e "$guarded_checkpoints/backed-target-absent.ready" ]] && break
      sleep 0.01
    done
    test -e "$guarded_checkpoints/backed-target-absent.ready"
    ln -s /nix/store/racer-home-manager-files/file \
      "$HOME/config with spaces/guarded-race"
    touch "$guarded_checkpoints/backed-target-absent.continue"
    if wait "$guarded_pid"; then
      echo "safe linker overwrote a guarded target created after its absence check" >&2
      exit 1
    fi
    test "$(readlink "$HOME/config with spaces/guarded-race")" = \
      /nix/store/racer-home-manager-files/file
    rm "$HOME/config with spaces/guarded-race"

    ln -s /nix/store/old-home-manager-files/managed \
      "$HOME/config with spaces/managed-link"
    ${safeLink}/bin/ln -Tsf "$TMPDIR/guard-source" \
      "$HOME/config with spaces/managed-link"
    test "$(readlink "$HOME/config with spaces/managed-link")" = "$TMPDIR/guard-source"

    managed_race_target="$HOME/config with spaces/managed-race"
    managed_race_checkpoints="$TMPDIR/managed-race-checkpoints"
    mkdir -p "$managed_race_checkpoints"
    ln -s /nix/store/old-home-manager-files/managed "$managed_race_target"
    HM_LINK_TEST_CHECKPOINT_DIR="$managed_race_checkpoints" \
      ${safeLink}/bin/ln -Tsf "$TMPDIR/guard-source" "$managed_race_target" &
    managed_race_pid=$!
    for attempt in $(seq 1 1000); do
      [[ -e "$managed_race_checkpoints/managed-target-recorded.ready" ]] && break
      sleep 0.01
    done
    test -e "$managed_race_checkpoints/managed-target-recorded.ready"
    ln -s "$TMPDIR/managed-competitor" "$TMPDIR/managed-competitor-link"
    mv -Tf -- "$TMPDIR/managed-competitor-link" "$managed_race_target"
    touch "$managed_race_checkpoints/managed-target-recorded.continue"
    if wait "$managed_race_pid"; then
      echo "safe linker accepted a changed managed target" >&2
      exit 1
    fi
    test "$(readlink "$managed_race_target")" = "$TMPDIR/managed-competitor"

    cleanup_target="$HOME/config with spaces/cleanup-race"
    cleanup_checkpoints="$TMPDIR/cleanup-race-checkpoints"
    mkdir -p "$cleanup_checkpoints"
    ln -s /nix/store/old-home-manager-files/cleanup "$cleanup_target"
    HM_REMOVE_TEST_CHECKPOINT_DIR="$cleanup_checkpoints" \
      ${safeRemove}/bin/rm -- "$cleanup_target" &
    cleanup_pid=$!
    for attempt in $(seq 1 1000); do
      [[ -e "$cleanup_checkpoints/remove-target-observed.ready" ]] && break
      sleep 0.01
    done
    test -e "$cleanup_checkpoints/remove-target-observed.ready"
    printf 'cleanup competitor\n' > "$TMPDIR/cleanup-competitor"
    mv -Tf -- "$TMPDIR/cleanup-competitor" "$cleanup_target"
    touch "$cleanup_checkpoints/remove-target-observed.continue"
    if wait "$cleanup_pid"; then
      echo "guarded cleanup removed a racing user path" >&2
      exit 1
    fi
    grep -qx 'cleanup competitor' "$cleanup_target"
    rm "$cleanup_target"
    ln -s /nix/store/old-home-manager-files/cleanup "$cleanup_target"
    ${safeRemove}/bin/rm -- "$cleanup_target"
    test ! -e "$cleanup_target"

    ln -s "$TMPDIR/unmanaged-original" "$HOME/config with spaces/unmanaged-link"
    ${safeLink}/bin/ln -Tsf "$TMPDIR/guard-source" \
      "$HOME/config with spaces/unmanaged-link"
    test "$(readlink "$HOME/config with spaces/unmanaged-link")" = "$TMPDIR/guard-source"
    test "$(readlink "$HOME/config with spaces/unmanaged-link.$HM_BACKUP_ID")" = \
      "$TMPDIR/unmanaged-original"
    rm "$HOME/config with spaces/unmanaged-link"

    ${restoreCollisions}/bin/hm-restore-backups
    test "$(readlink "$HOME/config with spaces/unmanaged-link")" = \
      "$TMPDIR/unmanaged-original"
    grep -qx original "$HOME/config with spaces/file"
    test ! -e "$HOME/config with spaces/file.$HM_BACKUP_ID"

    printf 'second original\n' > "$HOME/config with spaces/second"
    ${backupCollision}/bin/hm-backup-collision "$HOME/config with spaces/second"
    printf 'managed replacement\n' > "$HOME/config with spaces/second"
    ${restoreCollisions}/bin/hm-restore-backups
    grep -qx 'managed replacement' "$HOME/config with spaces/second"
    test -e "$HOME/config with spaces/second.$HM_BACKUP_ID"
    grep -qx pending "$HM_BACKUP_SESSION/status"

    rm "$HOME/config with spaces/second"
    ${restoreCollisions}/bin/hm-restore-backups
    grep -qx 'second original' "$HOME/config with spaces/second"
    test ! -e "$HOME/config with spaces/second.$HM_BACKUP_ID"
    grep -qx restored "$HM_BACKUP_SESSION/status"

    rollback_generation_1="$TMPDIR/generation-1"
    rollback_generation_2="$TMPDIR/generation-2"
    mkdir -p "$rollback_generation_1/home-files" "$rollback_generation_2/home-files"
    printf 'rollback original\n' > "$HOME/config with spaces/rollback"
    ${backupCollision}/bin/hm-backup-collision "$HOME/config with spaces/rollback"
    ${restoreCollisions}/bin/hm-restore-backups \
      --forward "" "$rollback_generation_1" "$rollback_generation_1"
    test ! -e "$HOME/config with spaces/rollback"
    ${restoreCollisions}/bin/hm-restore-backups \
      --forward "$rollback_generation_1" "$rollback_generation_2" "$rollback_generation_2"
    test ! -e "$HOME/config with spaces/rollback"
    ${restoreCollisions}/bin/hm-restore-backups \
      --rollback "$rollback_generation_2" "$rollback_generation_1" "$rollback_generation_1"
    grep -qx 'rollback original' "$HOME/config with spaces/rollback"

    printf 'declared original\n' > "$HOME/config with spaces/declared"
    ${backupCollision}/bin/hm-backup-collision "$HOME/config with spaces/declared"
    mkdir -p "$rollback_generation_1/home-files/config with spaces"
    printf 'managed\n' > "$rollback_generation_1/home-files/config with spaces/declared"
    ${restoreCollisions}/bin/hm-restore-backups \
      --rollback "$rollback_generation_2" "$rollback_generation_1" "$rollback_generation_1"
    test ! -e "$HOME/config with spaces/declared"
    grep -qx 'declared original' \
      "$HOME/config with spaces/declared.$HM_BACKUP_ID"

    ordered_home="$TMPDIR/ordered-home"
    ordered_state="$TMPDIR/ordered-state"
    ordered_target="$ordered_home/collision"
    mkdir -p "$ordered_home"
    printf 'older original\n' > "$ordered_target"
    HOME="$ordered_home" XDG_STATE_HOME="$ordered_state" \
      HM_BACKUP_ID=z-older \
      HM_BACKUP_SESSION="$ordered_state/home-manager/collision-backups/z-older" \
      ${backupCollision}/bin/hm-backup-collision "$ordered_target"
    printf 'newer original\n' > "$ordered_target"
    HOME="$ordered_home" XDG_STATE_HOME="$ordered_state" \
      HM_BACKUP_ID=a-newer \
      HM_BACKUP_SESSION="$ordered_state/home-manager/collision-backups/a-newer" \
      ${backupCollision}/bin/hm-backup-collision "$ordered_target"
    HOME="$ordered_home" XDG_STATE_HOME="$ordered_state" \
      ${restoreCollisions}/bin/hm-restore-backups
    grep -qx 'newer original' "$ordered_target"
    grep -qx 'older original' "$ordered_target.z-older"

    mkdir -p "$TMPDIR/link-source" "$TMPDIR/link-target"
    printf 'managed\n' > "$TMPDIR/link-source/managed"
    printf 'racer\n' > "$TMPDIR/link-target/managed"
    if ${safeLink}/bin/ln -sfn -t "$TMPDIR/link-target" -- "$TMPDIR/link-source/managed"; then
      echo "safe linker overwrote a target that appeared during activation" >&2
      exit 1
    fi
    grep -qx racer "$TMPDIR/link-target/managed"
    rm "$TMPDIR/link-target/managed"
    ${safeLink}/bin/ln -sfn -t "$TMPDIR/link-target" -- "$TMPDIR/link-source/managed"
    test -L "$TMPDIR/link-target/managed"

    printf 'source\n' > "$TMPDIR/rename-source"
    printf 'destination\n' > "$TMPDIR/rename-target"
    if ${renameNoReplace}/bin/hm-rename-no-replace \
      "$TMPDIR/rename-source" "$TMPDIR/rename-target"; then
      echo "atomic rename replaced an existing destination" >&2
      exit 1
    else
      test $? -eq 3
    fi
    grep -qx source "$TMPDIR/rename-source"
    grep -qx destination "$TMPDIR/rename-target"

    cat > "$TMPDIR/fail-rename" <<'EOF'
    #!${pkgs.bash}/bin/bash
    exit 1
    EOF
    chmod +x "$TMPDIR/fail-rename"
    printf 'journalled\n' > "$HOME/config with spaces/journalled"
    if HM_RENAME_NOREPLACE_BIN="$TMPDIR/fail-rename" \
      ${backupCollision}/bin/hm-backup-collision "$HOME/config with spaces/journalled"; then
      echo "backup unexpectedly succeeded with a failing rename" >&2
      exit 1
    fi
    grep -qx journalled "$HOME/config with spaces/journalled"

    cat > "$TMPDIR/racing-rename" <<'EOF'
    #!${pkgs.bash}/bin/bash
    printf 'competitor\n' > "$2"
    exit 3
    EOF
    chmod +x "$TMPDIR/racing-rename"
    printf 'race source\n' > "$HOME/config with spaces/race"
    if HM_RENAME_NOREPLACE_BIN="$TMPDIR/racing-rename" \
      ${backupCollision}/bin/hm-backup-collision "$HOME/config with spaces/race"; then
      echo "backup unexpectedly won a destination race" >&2
      exit 1
    fi
    rm "$HOME/config with spaces/race"
    ${restoreCollisions}/bin/hm-restore-backups
    test ! -e "$HOME/config with spaces/race"
    grep -qx competitor "$HOME/config with spaces/race.$HM_BACKUP_ID"

    cat > "$TMPDIR/crashing-rename" <<'EOF'
    #!${pkgs.bash}/bin/bash
    mv -- "$1" "$2"
    kill -KILL "$PPID"
    EOF
    chmod +x "$TMPDIR/crashing-rename"
    printf 'crash source\n' > "$HOME/config with spaces/crash"
    if HM_RENAME_NOREPLACE_BIN="$TMPDIR/crashing-rename" \
      ${backupCollision}/bin/hm-backup-collision "$HOME/config with spaces/crash"; then
      echo "backup unexpectedly survived its simulated crash" >&2
      exit 1
    fi
    test ! -e "$HOME/config with spaces/crash"
    ${restoreCollisions}/bin/hm-restore-backups
    grep -qx 'crash source' "$HOME/config with spaces/crash"

    mismatch_home="$TMPDIR/mismatch-home"
    mismatch_state="$TMPDIR/mismatch-state"
    mismatch_session="$mismatch_state/home-manager/collision-backups/mismatch"
    mkdir -p "$mismatch_home"
    printf 'prepared original\n' > "$mismatch_home/collision"
    cat > "$TMPDIR/crashing-mismatch-rename" <<'EOF'
    #!${pkgs.bash}/bin/bash
    printf 'racing replacement\n' > "$1.replacement"
    mv -Tf -- "$1.replacement" "$1"
    mv -- "$1" "$2"
    kill -KILL "$PPID"
    EOF
    chmod +x "$TMPDIR/crashing-mismatch-rename"
    if HOME="$mismatch_home" XDG_STATE_HOME="$mismatch_state" \
      HM_BACKUP_ID=mismatch HM_BACKUP_SESSION="$mismatch_session" \
      HM_RENAME_NOREPLACE_BIN="$TMPDIR/crashing-mismatch-rename" \
      ${backupCollision}/bin/hm-backup-collision "$mismatch_home/collision"; then
      echo "backup unexpectedly committed a mismatched prepared transaction" >&2
      exit 1
    fi
    if HOME="$mismatch_home" XDG_STATE_HOME="$mismatch_state" \
      ${restoreCollisions}/bin/hm-restore-backups; then
      echo "restore finalized an ambiguous prepared transaction" >&2
      exit 1
    fi
    grep -qx pending "$mismatch_session/status"
    grep -qx 'racing replacement' "$mismatch_home/collision.mismatch"
    test ! -e "$mismatch_home/collision"

    concurrent_home="$TMPDIR/concurrent-home"
    concurrent_state="$TMPDIR/concurrent-state"
    concurrent_session="$concurrent_state/home-manager/collision-backups/concurrent"
    mkdir -p "$concurrent_home"
    printf 'concurrent original\n' > "$concurrent_home/collision"
    cat > "$TMPDIR/slow-rename" <<EOF
    #!${pkgs.bash}/bin/bash
    touch "$TMPDIR/slow-rename-ready"
    sleep 1
    mv -- "\$1" "\$2"
    EOF
    chmod +x "$TMPDIR/slow-rename"
    env -u HM_BACKUP_ID -u HM_BACKUP_SESSION \
      HOME="$concurrent_home" XDG_STATE_HOME="$concurrent_state" \
      HM_BACKUP_ID=concurrent HM_BACKUP_SESSION="$concurrent_session" \
      HM_RENAME_NOREPLACE_BIN="$TMPDIR/slow-rename" \
      ${backupCollision}/bin/hm-backup-collision \
      "$concurrent_home/collision" &
    concurrent_backup_pid=$!
    while [[ ! -e "$TMPDIR/slow-rename-ready" ]]; do
      sleep 0.01
    done
    mkdir -p "$TMPDIR/concurrent-generation/home-files"
    HOME="$concurrent_home" XDG_STATE_HOME="$concurrent_state" \
      ${restoreCollisions}/bin/hm-restore-backups \
      --rollback /nix/store/generation-2 /nix/store/generation-1 \
      "$TMPDIR/concurrent-generation"
    wait "$concurrent_backup_pid"
    grep -qx 'concurrent original' "$concurrent_home/collision"
    grep -qx restored "$concurrent_session/status"

    guard_home="$TMPDIR/guard-home"
    guard_state="$TMPDIR/guard-state"
    mkdir -p "$guard_home"
    cat > "$TMPDIR/recreate-after-backup" <<EOF
    #!${pkgs.bash}/bin/bash
    ${backupCollision}/bin/hm-backup-collision "\$1"
    ln -s "$TMPDIR/guard-racer" "\$1"
    EOF
    chmod +x "$TMPDIR/recreate-after-backup"
    ln -s "$TMPDIR/guard-original" "$guard_home/collision"
    if env -u HM_BACKUP_ID -u HM_BACKUP_SESSION \
      HOME="$guard_home" XDG_STATE_HOME="$guard_state" \
      HM_LINK_ACTIVATION_ID=aborted-activation \
      HM_BACKUP_COMMAND="$TMPDIR/recreate-after-backup" \
      ${safeLink}/bin/ln -Tsf "$TMPDIR/guard-source" "$guard_home/collision"; then
      echo "safe linker overwrote a target recreated after backup" >&2
      exit 1
    fi
    test "$(readlink "$guard_home/collision")" = "$TMPDIR/guard-racer"
    guard_key=$(printf '%s' "$guard_home/collision" | sha256sum)
    guard_key=''${guard_key%% *}
    test ! -e \
      "$guard_state/home-manager/collision-backups/link-guards/aborted-activation/$guard_key"
    rm "$guard_home/collision"
    ln -s "$TMPDIR/guard-original-retry" "$guard_home/collision"
    env -u HM_BACKUP_ID -u HM_BACKUP_SESSION -u HM_BACKUP_COMMAND \
      HOME="$guard_home" XDG_STATE_HOME="$guard_state" \
      HM_LINK_ACTIVATION_ID=next-activation \
      ${safeLink}/bin/ln -Tsf "$TMPDIR/guard-source" "$guard_home/collision"
    test "$(readlink "$guard_home/collision")" = "$TMPDIR/guard-source"

    collision_home="$TMPDIR/collision-home"
    collision_files="$TMPDIR/collision-files"
    mkdir -p "$collision_home" "$collision_files"
    printf 'generated\n' > "$collision_files/foreign-link"
    printf 'foreign\n' > "$TMPDIR/foreign-link-source"
    ln -s "$TMPDIR/foreign-link-source" "$collision_home/foreign-link"
    HOME="$collision_home" \
      ${checkCollisions}/bin/hm-check-collisions \
      "$collision_files" "$collision_files/foreign-link"
    printf 'local\n' > "$collision_home/regular"
    printf 'generated\n' > "$collision_files/regular"
    if HOME="$collision_home" \
      ${checkCollisions}/bin/hm-check-collisions \
      "$collision_files" "$collision_files/regular"; then
      echo "collision check accepted an unprotected regular file" >&2
      exit 1
    fi
    HOME="$collision_home" HOME_MANAGER_BACKUP_COMMAND=/test/backup \
      ${checkCollisions}/bin/hm-check-collisions \
      "$collision_files" "$collision_files/regular"

    preflight_home="$TMPDIR/preflight-home"
    mkdir -p "$preflight_home/.agents/skills" "$TMPDIR/generated-skills"
    printf 'local\n' > "$preflight_home/.agents/skills/local"
    printf 'managed\n' > "$TMPDIR/generated-skills/managed"
    printf 'same\n' > "$preflight_home/identical"
    printf 'same\n' > "$TMPDIR/preflight-foreign-source"
    ln -s "$TMPDIR/preflight-foreign-source" "$preflight_home/foreign-link"
    cat > "$TMPDIR/fake-nix" <<'EOF'
    #!${pkgs.bash}/bin/bash
    while (($#)); do
      if [[ $1 == --out-link ]]; then
        out=$2
        break
      fi
      shift
    done
    generated_root="$out-generated"
    mkdir -p "$generated_root/.agents" "$out"
    ln -s "$PREFLIGHT_GENERATED_SKILLS" "$generated_root/.agents/skills"
    printf 'same\n' > "$generated_root/identical"
    printf 'same\n' > "$generated_root/foreign-link"
    ln -s "$generated_root" "$out/home-files"
    EOF
    chmod +x "$TMPDIR/fake-nix"
    preflight_output=$(
      HOME="$preflight_home" \
      NIX_BIN="$TMPDIR/fake-nix" \
      HM_STORE_DIR=/nix/store \
      PREFLIGHT_GENERATED_SKILLS="$TMPDIR/generated-skills" \
      bash ${../scripts/hm-preflight.sh} test-profile
    )
    case "$preflight_output" in
      *"COLLISION $preflight_home/.agents/skills"*) ;;
      *)
        printf 'preflight omitted directory collision:\n%s\n' "$preflight_output" >&2
        exit 1
        ;;
    esac
    case "$preflight_output" in
      *"COLLISION $preflight_home/identical"*) ;;
      *)
        printf 'preflight omitted equal-content regular collision:\n%s\n' \
          "$preflight_output" >&2
        exit 1
        ;;
    esac
    case "$preflight_output" in
      *"COLLISION $preflight_home/foreign-link"*) ;;
      *)
        printf 'preflight omitted equal-content symlink collision:\n%s\n' \
          "$preflight_output" >&2
        exit 1
        ;;
    esac
    grep -qx local "$preflight_home/.agents/skills/local"
    grep -qx same "$preflight_home/identical"
    test "$(readlink "$preflight_home/foreign-link")" = \
      "$TMPDIR/preflight-foreign-source"

    cloudtop_preflight_output=$(
      HOME="$preflight_home" \
      NIX_BIN="$TMPDIR/fake-nix" \
      HM_STORE_DIR=/nix/store \
      PREFLIGHT_GENERATED_SKILLS="$TMPDIR/generated-skills" \
      bash ${../scripts/hm-preflight.sh} ervin@cloudtop
    )
    case "$cloudtop_preflight_output" in
      *"INITIALIZE $preflight_home/.config/VSCodium/User/settings.json"*) ;;
      *)
        printf 'Cloudtop preflight omitted writable VSCodium initialization:\n%s\n' \
          "$cloudtop_preflight_output" >&2
        exit 1
        ;;
    esac

    lenovo_preflight_output=$(
      HOME="$preflight_home" \
      NIX_BIN="$TMPDIR/fake-nix" \
      HM_STORE_DIR=/nix/store \
      PREFLIGHT_GENERATED_SKILLS="$TMPDIR/generated-skills" \
      bash ${../scripts/hm-preflight.sh} ervin@lenovo
    )
    case "$lenovo_preflight_output" in
      *"INITIALIZE $preflight_home/.config/VSCodium/User/settings.json"*) ;;
      *)
        printf 'preflight omitted writable VSCodium initialization:\n%s\n' \
          "$lenovo_preflight_output" >&2
        exit 1
        ;;
    esac
    test ! -e "$preflight_home/.config/VSCodium/User/settings.json"

    fatal_home="$TMPDIR/fatal-home"
    fatal_state="$TMPDIR/fatal-state"
    fatal_target="$fatal_home/collision"
    mkdir -p "$fatal_home" "$fatal_state"
    printf 'must survive\n' > "$fatal_target"
    cat > "$TMPDIR/fatal-consumer" <<EOF
    #!${pkgs.bash}/bin/bash
    ${backupCollisionForActivation}/bin/hm-backup-collision-for-activation "$fatal_target"
    printf 'clobbered\n' > "$fatal_target"
    EOF
    chmod +x "$TMPDIR/fatal-consumer"
    if HOME="$fatal_home" XDG_STATE_HOME="$fatal_state" \
      HM_RENAME_NOREPLACE_BIN="$TMPDIR/fail-rename" \
      "$TMPDIR/fatal-consumer"; then
      echo "activation backup failure did not abort its command consumer" >&2
      exit 1
    fi
    grep -qx 'must survive' "$fatal_target"

    darwin_home="$TMPDIR/darwin-home"
    darwin_state="$TMPDIR/darwin-state"
    darwin_session="$darwin_state/home-manager/collision-backups/darwin-session"
    mkdir -p \
      "$darwin_home" \
      "$TMPDIR/darwin-generation-8/home-files" \
      "$TMPDIR/darwin-generation-9/home-files"
    printf 'managed\n' > "$TMPDIR/darwin-generation-9/home-files/collision"
    (
      export HOME="$darwin_home"
      export XDG_STATE_HOME="$darwin_state"
      export HM_BACKUP_ID=darwin-session
      export HM_BACKUP_SESSION="$darwin_session"
      printf 'darwin original\n' > "$darwin_home/collision"
      ${backupCollision}/bin/hm-backup-collision "$darwin_home/collision"
      ${restoreCollisions}/bin/hm-restore-backups \
        --forward /nix/store/darwin-generation-10 /nix/store/darwin-generation-9 \
        "$TMPDIR/darwin-generation-9"
      printf 'darwin managed\n' > "$darwin_home/collision"
      ${restoreCollisions}/bin/hm-restore-backups \
        --rollback /nix/store/darwin-generation-10 /nix/store/darwin-generation-9 \
        "$TMPDIR/darwin-generation-9"
      grep -qx 'darwin managed' "$darwin_home/collision"
      rm "$darwin_home/collision"
      ${restoreCollisions}/bin/hm-restore-backups \
        --rollback /nix/store/darwin-generation-9 /nix/store/darwin-generation-8 \
        "$TMPDIR/darwin-generation-8"
      grep -qx 'darwin original' "$darwin_home/collision"
    )

    cat > "$TMPDIR/fake-home-manager" <<'EOF'
    #!${pkgs.bash}/bin/bash
    printf '%s\0' "$@" > "$HM_TEST_ARGS"
    if [[ -n ''${HM_TEST_CURRENT_ROOT:-} && -n ''${HM_TEST_NEW_GENERATION:-} ]]; then
      ln -sfn "$HM_TEST_NEW_GENERATION" "$HM_TEST_CURRENT_ROOT"
    fi
    EOF
    chmod +x "$TMPDIR/fake-home-manager"
    mkdir -p \
      "$TMPDIR/switch-state/home-manager/gcroots" \
      "$TMPDIR/switch-generation-1" \
      "$TMPDIR/switch-generation-2"
    ln -s "$TMPDIR/switch-generation-2" \
      "$TMPDIR/switch-state/home-manager/gcroots/current-home"
    cat > "$TMPDIR/fake-restore" <<'EOF'
    #!${pkgs.bash}/bin/bash
    printf '%s\0' "$@" > "$HM_TEST_RESTORE_ARGS"
    EOF
    chmod +x "$TMPDIR/fake-restore"
    HM_TEST_ARGS="$TMPDIR/lenovo-args" \
      HM_TEST_RESTORE_ARGS="$TMPDIR/lenovo-restore-args" \
      HM_TEST_CURRENT_ROOT="$TMPDIR/switch-state/home-manager/gcroots/current-home" \
      HM_TEST_NEW_GENERATION="$TMPDIR/switch-generation-1" \
      XDG_STATE_HOME="$TMPDIR/switch-state" \
      HOME_MANAGER_BIN="$TMPDIR/fake-home-manager" \
      HM_BACKUP_COMMAND=/test/backup-command \
      HM_RESTORE_COMMAND="$TMPDIR/fake-restore" \
      HM_FLAKE="$TMPDIR/flake" \
      ${switchCommand}/bin/hm-switch ervin@lenovo --rollback
    mapfile -d "" -t switch_args < "$TMPDIR/lenovo-args"
    test "''${switch_args[0]}" = -B
    test "''${switch_args[1]}" = /test/backup-command
    test "''${switch_args[2]}" = switch
    test "''${switch_args[3]}" = --rollback
    test "''${switch_args[4]}" = --flake
    test "''${switch_args[5]}" = "$TMPDIR/flake#ervin@lenovo"
    mapfile -d "" -t restore_args < "$TMPDIR/lenovo-restore-args"
    test "''${restore_args[0]}" = --rollback
    test "''${restore_args[1]}" = "$TMPDIR/switch-generation-2"
    test "''${restore_args[2]}" = "$TMPDIR/switch-generation-1"
    test "''${restore_args[3]}" = "$TMPDIR/switch-generation-1"

    HM_TEST_ARGS="$TMPDIR/cloudtop-args" \
      HM_TEST_RESTORE_ARGS="$TMPDIR/cloudtop-restore-args" \
      XDG_STATE_HOME="$TMPDIR/switch-state" \
      HOME_MANAGER_BIN="$TMPDIR/fake-home-manager" \
      HM_BACKUP_COMMAND=/test/backup-command \
      HM_RESTORE_COMMAND="$TMPDIR/fake-restore" \
      HM_FLAKE="$TMPDIR/flake" \
      ${switchCommand}/bin/hm-switch ervin@cloudtop
    mapfile -d "" -t switch_args < "$TMPDIR/cloudtop-args"
    test "''${switch_args[0]}" = -B
    test "''${switch_args[1]}" = /test/backup-command
    test "''${switch_args[2]}" = switch
    test "''${switch_args[3]}" = --impure
    test "''${switch_args[4]}" = --flake
    test "''${switch_args[5]}" = "$TMPDIR/flake#ervin@cloudtop"

    mkdir -p \
      "$TMPDIR/darwin-generation-1" \
      "$TMPDIR/darwin-generation-2" \
      "$TMPDIR/darwin-home-generation/home-files" \
      "$TMPDIR/darwin-switch-state/home-manager/collision-backups"
    printf '%s\0' "$TMPDIR/old-darwin-home-generation" \
      >"$TMPDIR/darwin-switch-state/home-manager/collision-backups/active-managed-generation"
    ln -s "$TMPDIR/darwin-generation-2" "$TMPDIR/darwin-current-system"
    cat > "$TMPDIR/fake-sudo" <<'EOF'
    #!${pkgs.bash}/bin/bash
    exec "$@"
    EOF
    cat > "$TMPDIR/fake-darwin-rebuild" <<'EOF'
    #!${pkgs.bash}/bin/bash
    printf '%s\0' "$@" > "$DARWIN_TEST_ARGS"
    ln -sfn "$DARWIN_TEST_NEW_GENERATION" "$DARWIN_CURRENT_SYSTEM"
    managed_state_temporary="$DARWIN_TEST_MANAGED_STATE.$$"
    printf '%s\0' "$DARWIN_TEST_HOME_GENERATION" >"$managed_state_temporary"
    mv -f "$managed_state_temporary" "$DARWIN_TEST_MANAGED_STATE"
    EOF
    chmod +x "$TMPDIR/fake-sudo" "$TMPDIR/fake-darwin-rebuild"
    DARWIN_CURRENT_SYSTEM="$TMPDIR/darwin-current-system" \
      DARWIN_REBUILD_BIN="$TMPDIR/fake-darwin-rebuild" \
      DARWIN_TEST_ARGS="$TMPDIR/darwin-switch-args" \
      DARWIN_TEST_NEW_GENERATION="$TMPDIR/darwin-generation-1" \
      DARWIN_TEST_MANAGED_STATE="$TMPDIR/darwin-switch-state/home-manager/collision-backups/active-managed-generation" \
      DARWIN_TEST_HOME_GENERATION="$TMPDIR/darwin-home-generation" \
      HM_RESTORE_COMMAND="$TMPDIR/fake-restore" \
      HM_TEST_RESTORE_ARGS="$TMPDIR/darwin-restore-args" \
      XDG_STATE_HOME="$TMPDIR/darwin-switch-state" \
      HOME="$TMPDIR/darwin-switch-home" \
      SUDO_BIN="$TMPDIR/fake-sudo" \
      ${darwinSwitchCommand}/bin/darwin-switch --rollback
    mapfile -d "" -t darwin_args < "$TMPDIR/darwin-switch-args"
    test "''${darwin_args[0]}" = switch
    test "''${darwin_args[1]}" = --rollback
    mapfile -d "" -t restore_args < "$TMPDIR/darwin-restore-args"
    test "''${restore_args[0]}" = --rollback
    test "''${restore_args[1]}" = "$TMPDIR/darwin-generation-2"
    test "''${restore_args[2]}" = "$TMPDIR/darwin-generation-1"
    test "''${restore_args[3]}" = "$TMPDIR/darwin-home-generation"

    printf 'outside\n' > "$TMPDIR/outside"
    if ${backupCollision}/bin/hm-backup-collision "$TMPDIR/outside"; then
      echo "backup helper accepted a path outside HOME" >&2
      exit 1
    fi
    grep -qx outside "$TMPDIR/outside"

    touch "$out"
  '';
in
{
  inherit
    backupCollision
    checkCollisions
    backupCollisionForActivation
    darwinSwitchCommand
    preflight
    renameNoReplace
    restoreCollisions
    safeLink
    safeRemove
    switchCommand
    test
    ;
}
