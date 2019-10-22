import os
import secrets
import subprocess

from arrow.celery import app
from .models import Submission


# check_post_script = '''
# #!/bin/bash
# g++ -std=c++17 -static -o solution solution.cpp > checker_output
# g++ -std=c++17 -static -o checker checker.cpp > checker_output
#
# touch checker_output_file
# ./solution < usercode/input_file > answer_file
# ./checker usercode/input_file usercode/output_file answer_file checker_output_file
# printf $? > checker_result_file
#
# printf \"checker_result@checker_result_file\\n\" >> payload_files
# printf \"checker_output@checker_output_file\\n\" >> payload_files
# printf \"generator_errors@generator_errors_file\\n\" >> payload_files
# printf \"compilation_errors@compilation_errors_file\\n\" >> payload_files
# '''


# def python3_submission(submission, test):
#     return {
#         "container_wall_time_limit": 300,  # for whole execution
#         "wall_time_limit": 10,  # for isolate
#         "time_limit": submission.problem.time_limit,
#         "memory_limit": submission.problem.memory_limit,
#         "files": {
#             "usercode/code.py": str(submission.data),
#             "solution.cpp": str(submission.problem.solution),
#             "checker.cpp": str(submission.problem.checker),
#             "prepare.sh": '''''',
#             "usercode/input_file": str(test.data),
#             "post.sh": check_post_script
#         },
#         "run_command": '/usr/bin/python3 code.py'
#     }


def create_and_write_to_file(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        path = open(path, 'w')
        path.write(data)
        path.close()
    except IOError:
        return Exception(f'FAILED TO WRITE/OPEN FILE: {path}')


def cpp17_submission_compilation(app_path, folder, submission):
    create_and_write_to_file(f'{app_path}{folder}/submission.cpp',
                             submission.data)
    try:
        cp = subprocess.run(
            f'g++ -std=c++17 -static -lm -s -x c++ -W -O2 -std=c++17 -o usercode/submission submission.cpp',
            shell=True, capture_output=True, cwd=f'{app_path}{folder}',
            timeout=10)  # if too long then its bad
    except subprocess.TimeoutExpired:
        submission.testing = False
        submission.tested = True
        submission.verdict = Submission.CP
        submission.verdict_message = 'Compilation Error'
        submission.verdict_description = 'Compilation took too long'
        submission.save()
        return Submission.CP

    if cp.returncode != 0:
        submission.testing = False
        submission.tested = True
        submission.verdict = Submission.CP
        submission.verdict_message = 'Compilation Error'
        submission.verdict_description = cp.stdout.decode() + '\n' + cp.stderr.decode()
        submission.save()
        return Submission.CP


def python3_submission_compilation(app_path, folder, submission):
    create_and_write_to_file(f'{app_path}{folder}/usercode/submission.py',
                             submission.data)


compilation_dict = {
    Submission.CPP17: cpp17_submission_compilation,
    Submission.PYTHON3: python3_submission_compilation
}

run_command_dict = {
    Submission.CPP17: './submission',
    Submission.PYTHON3: '/usr/bin/python3.7 submission.py'
}


def run_judge_sandbox(submission, tests, app_path, folder):
    """
    copying payload, usercode and input to temp directory and
    setting permissions
    """
    container_wall_time_limit = 300  # 300 seconds
    memory_limit = submission.problem.memory_limit
    time_limit = submission.problem.time_limit
    wall_time_limit = 10  # 10 seconds

    # Copy payload folder at /app/polygon/payload
    cp = subprocess.run(
        f'mkdir {app_path}{folder} && cp -rp {app_path}payload/* {app_path}{folder}',
        shell=True)
    if cp.returncode != 0:
        raise Exception('Copy payload failed')

    # Copy user code and compile it
    if compilation_dict[submission.submission_type](app_path, folder,
                                                    submission) == Submission.CP:
        return Submission.CP
    print('User code compiled')

    # Copy solution checker and compile
    create_and_write_to_file(f'{app_path}{folder}/solution.cpp',
                             submission.problem.solution)
    create_and_write_to_file(f'{app_path}{folder}/checker.cpp',
                             submission.problem.checker)
    cp = subprocess.run(
        f'g++ -std=c++17 -static -o {app_path}{folder}/solution {app_path}{folder}/solution.cpp',
        shell=True, capture_output=True)
    if cp.returncode != 0:
        submission.testing = False
        submission.tested = True
        submission.verdict = Submission.TE
        submission.verdict_message = 'Test Error'
        submission.verdict_debug_message = 'Solution compilation error'
        submission.verdict_debug_description = cp.stdout.decode() + '\n' + cp.stderr.decode()
        submission.save()
        raise Exception('Solution compilation error')
    print('solution compiled')

    cp = subprocess.run(
        f'g++ -std=c++17 -static -o {app_path}{folder}/checker {app_path}{folder}/checker.cpp',
        shell=True, capture_output=True)
    if cp.returncode != 0:
        submission.testing = False
        submission.tested = True
        submission.verdict = Submission.TE
        submission.verdict_message = 'Test Error'
        submission.verdict_debug_message = 'Checker compilation error'
        submission.verdict_debug_description = cp.stdout.decode() + '\n' + cp.stderr.decode()
        submission.save()
        raise Exception('Checker compilation error')
    print('checker compiled')

    # Copy and compile generators
    for generator in submission.problem.generator_set.all():
        create_and_write_to_file(f'{app_path}{folder}/{generator.name}.cpp',
                                 generator.generator)
        cp = subprocess.run(
            f'g++ -std=c++17 -static -o {app_path}{folder}/{generator.name} {app_path}{folder}/{generator.name}.cpp',
            shell=True, capture_output=True)
        if cp.returncode != 0:
            submission.testing = False
            submission.tested = True
            submission.verdict = Submission.TE
            submission.verdict_message = 'Test Error'
            submission.verdict_debug_message = 'Generator compilation error'
            submission.verdict_debug_description = cp.stdout.decode() + '\n' + cp.stderr.decode()
            submission.save()
            raise Exception(f'Generator: {generator} compilation error')
        print(f'Generator: {generator.name} compiled')

    cp = subprocess.run(f'chmod -R 777 {app_path}{folder}',
                        shell=True)
    cp = subprocess.run(
        f'chmod -R 677 {app_path}{folder}/usercode', shell=True)
    cp = subprocess.run(
        f'chmod 677 {app_path}{folder}/usercode', shell=True)
    print('Files copied and compiled')

    # Ok, all sources compiled. Now we should test submission
    max_time_used = -1
    max_memory_used = -1
    for test in tests:
        # Notify user about test
        submission.testing_message = f'Testing on test #{test.index}'
        submission.save()
        # Prepare test input
        if test.use_generator:
            # Run generator
            cp = subprocess.run(
                f'{app_path}{folder}/{test.generator.name} {test.data} | tee {app_path}{folder}/usercode/input_file {app_path}{folder}/input_file',
                shell=True, capture_output=True)
            if cp.returncode != 0:
                submission.testing = False
                submission.tested = True
                submission.verdict = Submission.TE
                submission.verdict_message = 'Test Error'
                submission.verdict_debug_message = 'Test generation error'
                submission.verdict_debug_description = f'Generator exit code {cp.returncode}'
                submission.save()
                raise Exception(
                    f'Generator: {test.generator} runtime error\n Generator output: \n{cp.stdout.decode()}\n{cp.stderr.decode()}')
        else:
            # Copy test
            create_and_write_to_file(f'{app_path}{folder}/usercode/input_file',
                                     test.data)
            create_and_write_to_file(f'{app_path}{folder}/input_file',
                                     test.data)
        print(f'Test #{test.index} writen')
        # clean up
        subprocess.run(f'isolate --cleanup --cg', shell=True)
        # Run user code
        run_command = f'run_isolate.sh {app_path}{folder} {str(memory_limit)} {str(time_limit)} {wall_time_limit} {run_command_dict[submission.submission_type]}'
        try:
            subprocess.run(f'sh {app_path}{folder}/{run_command}',
                           timeout=container_wall_time_limit,
                           capture_output=True,
                           shell=True)
        except subprocess.TimeoutExpired:
            raise Exception('container_wall_time_limit exceeded')
        print(f'Successful execution')
        # Parse meta file
        raw_meta = str()
        try:
            fs = open(f'{app_path}{folder}/meta')
            raw_meta = fs.read()
        except IOError:
            print('FAILED TO WRITE/OPEN FILE: meta. some how sandbox failed')
            raise Exception(
                'FAILED TO WRITE/OPEN FILE: meta. some how sandbox failed')
        meta = dict()
        print(raw_meta)
        for i in raw_meta.split('\n'):
            if i != '':
                meta[i[0:i.find(':')]] = i[i.find(':') + 1:]

        # If meta fails => retry
        if 'status' in meta and meta['status'] == 'XX':
            submission.testing = False
            submission.tested = True
            submission.verdict = Submission.TE
            submission.verdict_message = 'Test Error'
            submission.verdict_debug_message = 'Meta status is XX'
            submission.save()
            raise Exception('Meta status is XX retrying...')

        meta_status = {
            'RE': Submission.RE,
            'TO': Submission.TLE,
            'SG': Submission.MLE,
            'XX': Submission.TE,
        }

        meta_status_verbose = {
            'RE': 'Runtime error',
            'TO': 'Time limit exceeded',
            'SG': 'Memory limit exceeded',
            'XX': 'Test error',
        }

        if 'status' in meta:
            if meta['status'] in meta_status:
                submission.verdict = meta_status[meta['status']]
                submission.verdict_message = \
                    f'{meta_status_verbose[meta["status"]]} on test #{test.index}'
                submission.testing = False
                submission.tested = True
                submission.save()
                return
        if 'time' in meta:
            max_time_used = max(max_time_used, float(meta['time']))
            submission.max_time_used = max_time_used
        if 'max-rss' in meta:
            max_memory_used = max(max_memory_used, int(meta['max-rss']))
            submission.max_memory_used = max_memory_used

        # OK now lets check result
        # First lest run solution
        cp = subprocess.run(
            f'{app_path}{folder}/solution < {app_path}{folder}/input_file > {app_path}{folder}/answer_file',
            shell=True)
        if cp.returncode != 0:
            submission.testing = False
            submission.tested = True
            submission.verdict = Submission.TE
            submission.verdict_message = 'Test Error'
            submission.verdict_debug_message = 'Test solution error'
            submission.verdict_debug_description = f'Solution exit code {cp.returncode}'
            submission.save()
            raise Exception(
                f'Solution runtime error')
        print('Solution executed')
        # Now lest run checker
        # ./checker usercode/input_file usercode/output_file answer_file
        cp = subprocess.run(
            f'{app_path}{folder}/checker {app_path}{folder}/input_file {app_path}{folder}/usercode/output_file {app_path}{folder}/answer_file',
            shell=True, capture_output=True)
        checker_result = cp.returncode
        checker_output = cp.stdout.decode() + '\n' + cp.stderr.decode()
        if cp.returncode == 3:
            submission.testing = False
            submission.tested = True
            submission.verdict = Submission.TE
            submission.verdict_message = 'Test Error'
            submission.verdict_debug_message = 'Checker error'
            submission.verdict_debug_description = checker_output
            submission.save()
            raise Exception(
                f'Checker fail: {checker_output}')
        print(checker_output)
        print(f'Checker executed')
        verdict_dict = {
            0: Submission.OK,
            1: Submission.WA,
            2: Submission.PE,
        }
        verbose = {
            0: 'Accepted',
            1: 'Wrong answer',
            2: 'Presentation error',
        }

        if checker_result != 0:
            if checker_result in verdict_dict:
                submission.verdict = verdict_dict[checker_result]
                submission.verdict_message = f'{verbose[checker_result]} on test #{test.index}'
                submission.testing = False
                submission.tested = True
                submission.save()
                return
            else:
                submission.verdict = Submission.UNKNOWN_CODE
                submission.verdict_message = f'{verbose[checker_result]} on test #{test.index}'
                submission.testing = False
                submission.tested = True
                submission.save()
                return
        print(f'Checker result: {checker_result}')
    submission.verdict = Submission.OK
    submission.verdict_message = f'Accepted'
    submission.testing = False
    submission.tested = True
    submission.save()
    return Submission.OK


@app.task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 5},
          default_retry_delay=10)
def judge_submission_task(submission_id):
    submission = Submission.objects.get(pk=submission_id)
    submission.erase_verdict()
    submission.tested = False
    submission.testing = True
    submission.save()

    tests = submission.problem.test_set.order_by('index')
    app_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    folder = 'temp/' + secrets.token_hex(16)

    if submission.submission_type in [Submission.CPP17, Submission.PYTHON3]:
        try:
            return run_judge_sandbox(submission, tests, app_path, folder)
        except Exception as e:
            subprocess.run(f'rm -rf {app_path}{folder}', shell=True)
            submission.testing = False
            submission.tested = True
            submission.verdict = Submission.TE
            submission.verdict_message = 'Test Error'
            submission.save()
            raise e
    return


@app.task
def sandbox_run_on_error(request, exc, traceback,
                         submission_id):
    print('Task {0!r} raised error: {1!r}'.format(request.id, exc))
    submission = Submission.objects.get(pk=submission_id)
    if submission:
        submission.testing = False
        submission.tested = True
        submission.verdict = submission.TE
        submission.verdict_message = f'Test failed, notify admin'
        submission.verdict_debug_description = str(traceback)
        submission.save()
